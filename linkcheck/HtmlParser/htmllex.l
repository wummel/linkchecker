/* Copyright (C) 2000-2006 Bastian Kleineidam

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
*/

/* Lexical analyzer for finding recognizable tokens in (probably
 * bad formatted) HTML streams.
 * Unrecognizable character data is passed on as a TEXT token.
 *
 * Note that you cannot rely on the "longest match" preference of
 * flex here since input data might be truncated at any given position.
 * This explains some of the more complicated lookahead rules below.
 */

%{
#include "htmlsax.h"
#include "s_util.h"
#include <string.h>
#include <stdlib.h>


/* token type */
#define YYSTYPE PyObject*
/* type of user-specified data */
#define YY_EXTRA_TYPE UserData*

/* Returning T_ERROR is the standard error-out reaction for this lexer. */
/* Return T_ERROR if argument is NULL. */
#define CHECK_NULL(a) \
    if ((a) == NULL) return T_ERROR

/* Return T_ERROR if argument is -1 (minus one). */
#define CHECK_MINUSONE(a) \
    if ((a) == -1) return T_ERROR

/* resize buffer b, returning T_ERROR on error */
#define RESIZE_BUF(b, n) \
    CHECK_NULL((b) = PyMem_Resize((b), char, (n))); \
    (b)[(n)-1] = '\0'

/* make python unicode string from tmp_buf and assign it to a */
#define PYSTRING_TMP_UNICODE(a) { \
    PyObject* pencoding; \
    char* encoding; \
    CHECK_NULL(pencoding = PyObject_GetAttrString(yyextra->parser, "encoding")); \
    encoding = PyString_AsString(pencoding); \
    if (encoding==NULL) { Py_DECREF(pencoding); return T_ERROR; } \
    (a) = PyUnicode_Decode(yyextra->tmp_buf, strlen(yyextra->tmp_buf),  \
                           encoding, "ignore"); \
    Py_DECREF(pencoding); \
    CHECK_NULL(a); \
}

#define PYSTRING_TMP_ASCII(a) \
    CHECK_NULL((a) = PyUnicode_Decode(yyextra->tmp_buf, \
          strlen(yyextra->tmp_buf), "ascii", "ignore"))

/* set return value from tmp_buf */
#define SETLVAL_UNICODE { \
    PyObject* s; \
    PYSTRING_TMP_UNICODE(s); \
    RESIZE_BUF(yyextra->tmp_buf, 1); \
    *yylval = s; \
    }

/* set return value from tmp_buf */
#define SETLVAL_ASCII { \
    PyObject* s; \
    PYSTRING_TMP_ASCII(s); \
    RESIZE_BUF(yyextra->tmp_buf, 1); \
    *yylval = s; \
    }

/* append yytext to tmp_buf */
#define APPEND_TO_TMP(n) { \
    size_t len = strlen(yyextra->tmp_buf) + (n) + 1; \
    RESIZE_BUF(yyextra->tmp_buf, len); \
    strlcat(yyextra->tmp_buf, yytext, len); \
    }

/* lowercase the tmp_buf */
#define LOWER_TMP { \
    char* p = yyextra->tmp_buf; \
    while (*p) { *p = tolower(*p); p++; } \
    }

/* check for JavaScript or CSS tags; must be before SET_ATTR_LVAL */
#define SCRIPT_CHECK { \
    PyObject* tagname; \
    CHECK_NULL(tagname = PyUnicode_AsEncodedString(yyextra->tmp_tag, "ascii", "ignore")); \
    if (strcmp("script", PyString_AsString(tagname))==0) \
	BEGIN(S_SCRIPT); \
    else if (strcmp("style", PyString_AsString(tagname))==0) \
        BEGIN(S_STYLE); \
    else \
	BEGIN(INITIAL); \
    Py_DECREF(tagname); \
    }

/* set return value from tag with attributes */
#define SET_ATTR_LVAL \
    if (yyextra->tmp_tag==NULL || yyextra->tmp_attrs==NULL) { \
        PyErr_SetString(PyExc_TypeError, "tmp_tag or tmp_attrs is NULL"); \
        return T_ERROR; \
    } \
    CHECK_NULL(*yylval = Py_BuildValue("(OO)", yyextra->tmp_tag, yyextra->tmp_attrs)); \
    yyextra->tmp_tag = yyextra->tmp_attrs = NULL

/* store collected name as attribute in dictionary
 * tmp_attrname and tmp_attrval must be NULL
 */
#define FLUSH_ATTRS \
    if (strlen(yyextra->tmp_buf) > 0) { \
        PYSTRING_TMP_UNICODE(yyextra->tmp_attrname); \
	RESIZE_BUF(yyextra->tmp_buf, 1); \
        CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname, Py_None)); \
        Py_CLEAR(yyextra->tmp_attrname); \
    }

/* update the buffer and scanner positions */
#define UPDATE_BUFPOS yyextra->bufpos += yyleng; yyextra->pos += yyleng

/* update the column position; use this *only* in rules that cannot match
 the newline char '\n'!
 */
#define UPDATE_COLUMN UPDATE_BUFPOS; yyextra->column += yyleng

/* update the line and column position; use this in rules that can match the
 newline char '\n'.
 */
#define UPDATE_LINE UPDATE_BUFPOS; { \
    int i; \
    for (i=0; i<yyleng; ++i) { \
        if (yytext[i] == '\n') { \
            ++(yyextra->lineno); \
            yyextra->column = 1; \
        } \
        else ++(yyextra->column); \
    } \
}

/* return a token, setting the nextpos value back to the bufpos */
#define RETURN(tok) yyextra->nextpos = yyextra->bufpos; return tok

/* use Pythons memory management */
void* yyalloc (yy_size_t bytes, void* yyscanner) {
    return PyMem_Malloc((size_t)bytes);
}
void* yyrealloc (void* ptr, yy_size_t bytes, void* yyscanner) {
    return PyMem_Realloc(ptr, (size_t)bytes);
}
void yyfree (void* ptr, void* yyscanner) {
    PyMem_Free(ptr);
}

/* include bison-generated token definitions */
#include "htmlparse.h"
%}

/* use our own memory management functions (see above) */
%option noyyalloc noyyrealloc noyyfree
/* handle 8bit characters */
%option 8bit
/* define output file */
%option outfile="htmllex.c"
/* optimize for speed */
%option align full
/* add debugging ability */
%option debug
/* don't use unneeded functions */
%option nounput nomain noyywrap noyymore noreject
/* make it reentrant and bison compatible */
%option bison-bridge reentrant never-interactive
/* print warnings on compiling */
%option warn

/* scanner states */
%x S_PI
%x S_COMMENT
%x S_COMMENT1
%x S_COMMENT2
%x S_DOCTYPE
%x S_CDATA
%x S_TAGSTART
%x S_TAGEND
%x S_TAGEND2
%x S_SCRIPT
%x S_SCRIPT_APOS
%x S_SCRIPT_APOS_ESC
%x S_SCRIPT_STRING
%x S_SCRIPT_STRING_ESC
%x S_SCRIPT_COMMENT
%x S_SCRIPT_MCOMMENT
%x S_STYLE
%x S_ATTR1
%x S_ATTR2
%x S_ATTR3
%x S_ATTR4
%x S_ATTR5
%x S_APOSSTRING
%x S_APOSSTRING_ESC
%x S_STRING
%x S_STRING_ESC

/* regular expression definitions used below */
RX_WHITE_SPACE	[\n\r\ \t\b\012]
RX_EQUAL =
RX_NAME	 [a-zA-Z]([-a-zA-Z0-9_])*
RX_DATA  [-a-zA-Z0-9_:]+

%%

  /*********************** EOF ************************/
<<EOF>> {
    /* hit end-of-file, wait for more data */
    return T_WAIT;
}

  /*********************** COMMENT ************************/
  /* Note: also accept "<! --" and "<!- " */
<INITIAL><!-- {
    UPDATE_COLUMN;
    BEGIN(S_COMMENT);
}

<INITIAL><![ ]+-- {
    UPDATE_COLUMN;
    BEGIN(S_COMMENT);
}

<INITIAL><!-/[ ] {
    UPDATE_COLUMN;
    BEGIN(S_COMMENT1);
}

<S_COMMENT>--> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_COMMENT);
}

<S_COMMENT>--[ ]+> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_COMMENT);
}

<S_COMMENT1>-> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_COMMENT);
}

<S_COMMENT,S_COMMENT1>-/-- {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT,S_COMMENT1>-/[^-] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT,S_COMMENT1>--/[^- >] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT,S_COMMENT1>--[ ]+/[^ >] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT,S_COMMENT1>[^-]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT,S_COMMENT1>. {
    return T_WAIT;
}

   /* Note: www.nba.com had some <! Copyright !> comment */
<INITIAL><![ ]+/[^-] {
    UPDATE_COLUMN;
    BEGIN(S_COMMENT2);
}

<S_COMMENT2>!> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_COMMENT);
}

<S_COMMENT2>[^!]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT2>![^>]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT2>. {
    return T_WAIT;
}


  /*********************** DOCTYPE ************************/
<INITIAL><![Dd][Oo][Cc][Tt][Yy][Pp][Ee] {
    UPDATE_COLUMN;
    BEGIN(S_DOCTYPE);
}

<S_DOCTYPE>> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_DOCTYPE);
}

<S_DOCTYPE>[^>]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

  /*********************** CDATA ************************/
<INITIAL><!\[CDATA\[ {
    UPDATE_COLUMN;
    BEGIN(S_CDATA);
}

<S_CDATA>\]*\]\]> {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng-3);
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_CDATA);
}

<S_CDATA>[^\]]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_CDATA>\]+[^>\]]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_CDATA>. {
    return T_WAIT;
}

  /*********************** PI ************************/
<INITIAL><\? {
    UPDATE_COLUMN;
    BEGIN(S_PI);
}

<S_PI>[^?>]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_PI>\?+> {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng-2);
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_PI);
}

<S_PI>\?+[^?>]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_PI>> {
    UPDATE_COLUMN;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_PI);
}

<S_PI>. {
    return T_WAIT;
}


  /*********************** TAGSTART ************************/
<INITIAL><{RX_WHITE_SPACE}*/[A-Za-z0-9] {
    UPDATE_LINE;
    CHECK_NULL(yyextra->tmp_attrs = PyObject_CallObject(yyextra->list_dict, NULL));
    BEGIN(S_TAGSTART);
}

<S_TAGSTART>[^ \t\r\n\b\012/<>]+ {
    /* actually accept a lot of tag chars, which may be illegal,
     but we dont care, it's the browsers job */
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_TAGSTART>{RX_WHITE_SPACE}+ {
    UPDATE_LINE;
    LOWER_TMP;
    PYSTRING_TMP_ASCII(yyextra->tmp_tag);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    BEGIN(S_ATTR1);
}

<S_TAGSTART>\/> {
    UPDATE_COLUMN;
    BEGIN(INITIAL);
    if (!strlen(yyextra->tmp_buf)) {
        /* the tag name was empty, assume a stray "</>" */
	RESIZE_BUF(yyextra->tmp_buf, 4);
        strcpy(yyextra->tmp_buf, "</>");
        yyextra->tmp_attrs = NULL;
        SETLVAL_UNICODE;
        RETURN(T_TEXT);
    }
    LOWER_TMP;
    PYSTRING_TMP_ASCII(yyextra->tmp_tag);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_TAGSTART>> {
    UPDATE_COLUMN;
    BEGIN(INITIAL);
    if (!strlen(yyextra->tmp_buf)) {
        /* the tag name was empty, assume a stray "<>" */
	RESIZE_BUF(yyextra->tmp_buf, 3);
        strcpy(yyextra->tmp_buf, "<>");
        yyextra->tmp_attrs = NULL;
	SETLVAL_UNICODE;
        RETURN(T_TEXT);
    }
    LOWER_TMP;
    PYSTRING_TMP_ASCII(yyextra->tmp_tag);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_TAGSTART>. {
    return T_WAIT;
}

  /*********************** SCRIPT ************************/
<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp][Tt]{RX_WHITE_SPACE}*> {
    UPDATE_LINE;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_SCRIPT);
}

<S_SCRIPT>[^/'"<]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT>\' {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_APOS);
}

<S_SCRIPT>\" {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_STRING);
}

<S_SCRIPT>\/\/ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_COMMENT);
}

<S_SCRIPT>\/\* {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_MCOMMENT);
}

<S_SCRIPT>\/[^*/] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

  /* XXX is there a better way to ensure any prefix of </script> is matched,
    but not </script> itself? */
<S_SCRIPT></[^/] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*/[^Ss] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss]/[^Cc] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc]/[^Rr] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr]/[^Ii] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii]/[^Pp] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp]/[^Tt] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp][Tt]{RX_WHITE_SPACE}*/[^>] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT>. {
    return T_WAIT;
}

<S_SCRIPT_APOS>\\ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_APOS_ESC);
}

<S_SCRIPT_APOS>[^\\']+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT_APOS>\' {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT);
}

<S_SCRIPT_APOS_ESC>. {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_APOS);
}

<S_SCRIPT_STRING>\\ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_STRING_ESC);
}

<S_SCRIPT_STRING>[^\\"]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT_STRING>\" {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT);
}

<S_SCRIPT_STRING_ESC>. {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT_STRING);
}

<S_SCRIPT_COMMENT>[^\-\r\n]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT_COMMENT>[\r\n] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT);
}

<S_SCRIPT_COMMENT>-([^-\r\n]+|-[^>\r\n]+) {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT_COMMENT>--> {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT);
}

<S_SCRIPT_COMMENT>. {
    return T_WAIT;
}

<S_SCRIPT_MCOMMENT>[^*]+|\* {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT_MCOMMENT>\*\/ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_SCRIPT);
}

  /*********************** STYLE ************************/
<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll][Ee]{RX_WHITE_SPACE}*> {
    UPDATE_LINE;
    SETLVAL_UNICODE;
    BEGIN(INITIAL);
    RETURN(T_STYLE);
}

<S_STYLE>[^<]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

  /* this is so shitty */
<S_STYLE></[^/] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*/[^Ss] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss]/[^Tt] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt]/[^Yy] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy]/[^Ll] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll]/[^Ee] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll][Ee]{RX_WHITE_SPACE}*/[^>] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE>. {
    return T_WAIT;
}

  /*********************** ATTRS ************************/
<S_ATTR1>{RX_NAME} {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR2);
}

<S_ATTR1,S_ATTR2,S_ATTR3>\/> {
    UPDATE_COLUMN;
    FLUSH_ATTRS;
    BEGIN(INITIAL);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_ATTR1,S_ATTR2,S_ATTR3>\/[^>] {
    UPDATE_LINE;
}

<S_ATTR1,S_ATTR2,S_ATTR3>\/ {
    return T_WAIT;
}

<S_ATTR1,S_ATTR2,S_ATTR3>> {
    UPDATE_COLUMN;
    FLUSH_ATTRS;
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR2>{RX_DATA} {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_ATTR2>\\\r?\n {
    /* Line continuations */
    UPDATE_LINE;
}

<S_ATTR2>\\\r?[^\n] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_ATTR2>\\\r? {
    return T_WAIT;
}

<S_ATTR2>{RX_WHITE_SPACE}+ {
    UPDATE_LINE;
    BEGIN(S_ATTR3);
}

<S_ATTR2,S_ATTR3>{RX_WHITE_SPACE}*{RX_EQUAL}{RX_WHITE_SPACE}* {
    UPDATE_LINE;
    LOWER_TMP;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrname);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    BEGIN(S_ATTR4);
}

<S_ATTR3>{RX_NAME} {
    UPDATE_COLUMN;
    LOWER_TMP;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrname);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    if (yyextra->tmp_attrval != NULL) return T_ERROR;
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname, Py_None));
    Py_CLEAR(yyextra->tmp_attrname);
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR2);
}

<S_ATTR1,S_ATTR2,S_ATTR3>.|\n {
    /* this also skips whitespace! */
    UPDATE_LINE;
}

<S_ATTR4>\\\" {
    /* backslash escapes seen at freshmeat.net */
    UPDATE_COLUMN;
    BEGIN(S_STRING);
}

<S_ATTR4>\" {
    UPDATE_COLUMN;
    BEGIN(S_STRING);
}

<S_ATTR4>\' {
    UPDATE_COLUMN;
    BEGIN(S_APOSSTRING);
}

<S_ATTR4>[^\012 \t\b\r\n>\'\"]+ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR5);
}

<S_ATTR4>> {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR4>{RX_WHITE_SPACE}+ {
    UPDATE_LINE;
}

<S_ATTR5>[^\012 \t\b\r\n>\"]+ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_ATTR5>> {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR5>\/> {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    BEGIN(INITIAL);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_ATTR5>[\"] {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    BEGIN(S_ATTR1);
}

<S_ATTR5>{RX_WHITE_SPACE}+ {
    UPDATE_LINE;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    BEGIN(S_ATTR1);
}

<S_APOSSTRING>\\/\r?[^\n] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_APOSSTRING_ESC);
}

<S_APOSSTRING>\\ {
    return T_WAIT;
}

<S_APOSSTRING>\' {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    BEGIN(S_ATTR1);
}

<S_APOSSTRING>[^\\']+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}


<S_APOSSTRING_ESC>. {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_APOSSTRING);
}

<S_STRING>\\?\" {
    UPDATE_COLUMN;
    PYSTRING_TMP_UNICODE(yyextra->tmp_attrval);
    RESIZE_BUF(yyextra->tmp_buf, 1);
    CHECK_NULL(yyextra->tmp_attrval = PyObject_CallFunction(yyextra->resolve_entities,
                                                 "O", yyextra->tmp_attrval));
    CHECK_MINUSONE(PyObject_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname,
                                    yyextra->tmp_attrval));
    Py_CLEAR(yyextra->tmp_attrname);
    Py_CLEAR(yyextra->tmp_attrval);
    BEGIN(S_ATTR1);
}

<S_STRING>\\/\r?[^\n] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_STRING_ESC);
}

<S_STRING,S_APOSSTRING>\\\r?\n {
    UPDATE_LINE;
}

<S_STRING>\\ {
    return T_WAIT;
}

<S_STRING>[^\\"]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
}

<S_STRING_ESC>. {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_STRING);
}


  /*********************** TAGEND ************************/
<INITIAL><{RX_WHITE_SPACE}*\/{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_LINE;
    BEGIN(S_TAGEND);
}

<S_TAGEND>[^<>\r\n \t\b\012]+ {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
}

<S_TAGEND>{RX_WHITE_SPACE}*> {
    UPDATE_LINE;
    LOWER_TMP;
    SETLVAL_ASCII;
    BEGIN(INITIAL);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND><{RX_WHITE_SPACE}*\/{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_LINE;
    LOWER_TMP;
    SETLVAL_ASCII;
    BEGIN(S_TAGEND);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND><{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_LINE;
    LOWER_TMP;
    SETLVAL_ASCII;
    CHECK_NULL(yyextra->tmp_attrs = PyObject_CallObject(yyextra->list_dict, NULL));
    BEGIN(S_TAGSTART);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND>{RX_WHITE_SPACE}+ {
    UPDATE_LINE;
    /* ignore any trailing garbage of this end tag */
    BEGIN(S_TAGEND2);
}

<S_TAGEND>. {
    return T_WAIT;
}

<S_TAGEND2>> {
    UPDATE_COLUMN;
    LOWER_TMP;
    SETLVAL_ASCII;
    BEGIN(INITIAL);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND2>[^<>]+ {
    UPDATE_LINE;
}

<S_TAGEND2><{RX_WHITE_SPACE}*\/{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_LINE;
    LOWER_TMP;
    SETLVAL_ASCII;
    BEGIN(S_TAGEND);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND2><{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_LINE;
    LOWER_TMP;
    SETLVAL_ASCII;
    CHECK_NULL(yyextra->tmp_attrs = PyObject_CallObject(yyextra->list_dict, NULL));
    BEGIN(S_TAGSTART);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND2>. {
    return T_WAIT;
}
  /*********************** TEXT ************************/
<INITIAL>[^<]+ {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    SETLVAL_UNICODE;
    RETURN(T_TEXT);
}

<INITIAL><[^\012 \t\b\r\nA-Za-z!?/] {
    UPDATE_COLUMN;
    APPEND_TO_TMP(yyleng);
    SETLVAL_UNICODE;
    RETURN(T_TEXT);
}

<INITIAL><{RX_WHITE_SPACE}+[^A-Za-z/] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    SETLVAL_UNICODE;
    RETURN(T_TEXT);
}
<INITIAL><![^- dD\[] {
    UPDATE_LINE;
    APPEND_TO_TMP(yyleng);
    SETLVAL_UNICODE;
    RETURN(T_TEXT);
}

<INITIAL>. {
    return T_WAIT;
}

%%

/* initialize the scanner */
int htmllexInit (void** scanner, UserData* data) {
    yylex_init(scanner);
    yyset_extra(data, *scanner);
    return 0;
}

/* set debug level; a level > 0 enables debugging */
int htmllexDebug (void** scanner, int debug) {
    int old = yyget_debug(*scanner);
    yyset_debug(debug, *scanner);
    return old;
}

/* prepare scanner for calls to yylex() */
int htmllexStart (void* scanner, UserData* data, const char* s, int slen) {
    /* append s to data buffer and scan those bytes.
     As Flex does not distinguish between NUL and EOF characters,
     replace NUL with ' '. */
    int len = strlen(data->buf);
    int i;
    RESIZE_BUF(data->buf, len + slen + 1);
    for (i=0; i < slen; i++) {
        data->buf[len+i] = (s[i]=='\0' ? ' ' : s[i]);
    }
    data->buf[len+slen] = '\0';
    if (yyget_debug(scanner)) {
        fprintf(stderr, "SCANBUF %d `%s'\n", data->bufpos, data->buf);
    }
    if (len > data->bufpos) {
        int rewind = len - data->bufpos;
        if (yyget_debug(scanner)) {
            fprintf(stderr, "REWIND %d\n", rewind);
        }
	slen += rewind;
	len -= rewind;
    }
    /* reset userdata */
    data->bufpos = len;
    data->exc_type = NULL;
    data->exc_val = NULL;
    data->exc_tb = NULL;
    if (yyget_debug(scanner)) {
        fprintf(stderr, "SCANNING `%s'\n", data->buf + len);
    }
    data->lexbuf = yy_scan_bytes(data->buf + len, slen, scanner);
    return 0;
}

/* delete scanned buffer data */
int htmllexStop (void* scanner, UserData* data) {
    yy_delete_buffer(data->lexbuf, scanner);
    if (data->nextpos > 0) {
	int len = strlen(data->buf);
	int i, j;
	for (i=data->nextpos, j=0; i<len; i++, j++) {
            data->buf[j] = data->buf[i];
	}
	data->buf[j] = '\0';
        /* Can return T_ERROR, which is guaranteed to be non-zero. */
	RESIZE_BUF(data->buf, len-data->nextpos + 1);
        data->bufpos -= data->nextpos;
	data->nextpos = 0;
    }
    return 0;
}

/* destroy scanner when not needed any more */
int htmllexDestroy (void* scanner) {
    yylex_destroy(scanner);
    return 0;
}
