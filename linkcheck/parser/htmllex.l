/* Find recognizable tokens in (probably bad formatted) HTML streams.
   Unrecognizable character data is passed on as a TEXT token. 
*/

%{
#include <string.h>
#include <stdlib.h>
#include "htmlsax.h"

#define YYSTYPE PyObject*
#define YY_EXTRA_TYPE UserData*

/* reset buffer a to empty string */
#define CLEAR_BUF(a) \
    a = PyMem_Resize(a, char, 1); \
    if (a==NULL) return T_ERROR; \
    a[0] = '\0'

/* make python string from tmp_buf and assign it to a */
#define PYSTRING_TMP(a) \
    a = PyString_FromString(yyextra->tmp_buf); \
    if (a==NULL) return T_ERROR

/* set return value from tmp_buf */
#define SETLVAL {\
    PyObject* s; \
    PYSTRING_TMP(s); \
    CLEAR_BUF(yyextra->tmp_buf); \
    *yylval = s; \
    }

/* append yytext to tmp_buf */
#define APPEND_TO_TMP(n) {\
    int len = strlen(yyextra->tmp_buf); \
    yyextra->tmp_buf = PyMem_Resize(yyextra->tmp_buf, char, len+n+1); \
    strncat(yyextra->tmp_buf, yytext, n); \
    }

/* lowercase the tmp_buf */
#define LOWER_TMP {\
    char* p = yyextra->tmp_buf; \
    while (*p) { *p = tolower(*p); p++; } \
    }

/* check for JavaScript or CSS tags; must be before SET_ATTR_LVAL */
#define SCRIPT_CHECK \
    if (strcmp("script", PyString_AS_STRING(yyextra->tmp_tag))==0) \
	BEGIN(S_SCRIPT); \
    else if (strcmp("style", PyString_AS_STRING(yyextra->tmp_tag))==0) \
        BEGIN(S_STYLE); \
    else \
	BEGIN(INITIAL)

/* set return value from tag with attributes */
#define SET_ATTR_LVAL \
    if (yyextra->tmp_tag==NULL || yyextra->tmp_attrs==NULL) { \
    PyErr_SetString(PyExc_TypeError, "tmp_tag or tmp_attrs is NULL"); \
    return T_ERROR; \
    } \
    *yylval = Py_BuildValue("(OO)", yyextra->tmp_tag, yyextra->tmp_attrs); \
    if ((*yylval)==NULL) return T_ERROR; \
    yyextra->tmp_tag = yyextra->tmp_attrs = NULL

/* store collected name as attribute in dictionary
 * tmp_attrname and tmp_attrval must be NULL
 */
#define FLUSH_ATTRS \
    if (strlen(yyextra->tmp_buf) > 0) { \
        PYSTRING_TMP(yyextra->tmp_attrname); \
	CLEAR_BUF(yyextra->tmp_buf); \
        if (PyDict_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname, Py_None)==-1) return T_ERROR; \
        Py_DECREF(yyextra->tmp_attrname); \
        yyextra->tmp_attrname = NULL; \
    }

/* update the buffer position */
#define UPDATE_BUFPOS yyextra->bufpos += yyleng
/* return a token, adjusting the nextpos value */
#define RETURN(tok) yyextra->nextpos = yyextra->bufpos; return tok

/* XXX todo */
#define SET_ERROR(s)

/* use Pythons memory management */
#define malloc PyMem_Malloc
#define realloc PyMem_Realloc
#define free PyMem_Free

#include "htmlparse.h"

/* Find out if and how we must quote the value as an HTML attribute.
 - quote if it contains white space or <>
 - quote with " if it contains '
 - quote with ' if it contains "

 val is a Python String object
*/
static PyObject* quote_string (PyObject* val) {
    char* quote = NULL;
    int len = PyString_GET_SIZE(val);
    char* internal = PyString_AS_STRING(val);
    int i;
    PyObject* prefix;
    for (i=0; i<len; i++) {
	if (!quote && (isspace(internal[i]) ||
		       internal[i]=='<' ||
		       internal[i]=='>')) {
            quote = "\"";
	}
	else if (internal[i]=='\'') {
	    quote = "\"";
            break;
	}
	else if (internal[i]=='"') {
	    quote = "'";
            break;
	}
    }
    if (quote==NULL) {
        return val;
    }
    /* quote suffix */
    if ((prefix = PyString_FromString(quote))==NULL) return NULL;
    PyString_Concat(&val, prefix);
    if (val==NULL) {
        Py_DECREF(prefix);
	return NULL;
    }
    /* quote prefix */
    PyString_ConcatAndDel(&prefix, val);
    if (prefix==NULL) {
        Py_DECREF(val);
	return NULL;
    }
    return prefix;
}
%}

%option 8bit outfile="htmllex.c"
%option align full
/* uncomment the next line for debugging */
/*%option debug*/
%option nounput nomain noyywrap noyymore noreject
%option bison-bridge reentrant never-interactive
%option warn

%x S_PI
%x S_COMMENT
%x S_DOCTYPE
%x S_CDATA
%x S_TAGSTART
%x S_TAGEND
%x S_SCRIPT
%x S_STYLE
%x S_ATTR1
%x S_ATTR2
%x S_ATTR3
%x S_ATTR4
%x S_ATTR5
%x S_APOSSTRING
%x S_STRING

RX_WHITE_SPACE	[\n\r\ \t\b\012]
RX_EQUAL	=
RX_NAME	[a-zA-Z]([-a-zA-Z0-9_])*
RX_DATA [-a-zA-Z0-9_]+

%%

  /*********************** EOF ************************/
<<EOF>> {
    /* wait for more data */
    return T_WAIT;
}

  /*********************** COMMENT ************************/
<INITIAL><!-- {
    UPDATE_BUFPOS;
    BEGIN(S_COMMENT);
}

<S_COMMENT>-*--> {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng-3);
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_COMMENT);
}

<S_COMMENT>[^-]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT>-+[^->]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_COMMENT>. {
    return T_WAIT;
}

  /*********************** DOCTYPE ************************/
<INITIAL><![Dd][Oo][Cc][Tt][Yy][Pp][Ee] {
    UPDATE_BUFPOS;
    BEGIN(S_DOCTYPE);
}

<S_DOCTYPE>> {
    UPDATE_BUFPOS;
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_DOCTYPE);
}

<S_DOCTYPE>[^>]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

  /*********************** CDATA ************************/
<INITIAL><!\[CDATA\[ {
    UPDATE_BUFPOS;
    BEGIN(S_CDATA);
}

<S_CDATA>\]*\]\]> {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng-3);
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_CDATA);
}

<S_CDATA>[^\]]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_CDATA>\]+[^>\]]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_CDATA>. {
    return T_WAIT;
}

  /*********************** PI ************************/
<INITIAL><\? {
    UPDATE_BUFPOS;
    BEGIN(S_PI);
}

<S_PI>\?*\?> {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng-2);
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_PI);
}

<S_PI>[^?]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_PI>\?+[^?>]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_PI>. {
    return T_WAIT;
}


  /*********************** TAGSTART ************************/
<INITIAL><{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_BUFPOS;
    yyextra->tmp_attrs = PyDict_New();
    if (yyextra->tmp_attrs==NULL) return T_ERROR;
    BEGIN(S_TAGSTART);
}

<S_TAGSTART>[^ \t\r\n\b\012/<>]+ {
    /* actually accept a lot of tag chars, which may be illegal,
     but we dont care, its the browsers job */
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_TAGSTART>{RX_WHITE_SPACE}+ {
    UPDATE_BUFPOS;
    LOWER_TMP;
    PYSTRING_TMP(yyextra->tmp_tag);
    CLEAR_BUF(yyextra->tmp_buf);
    BEGIN(S_ATTR1);
}

<S_TAGSTART>\/> {
    UPDATE_BUFPOS;
    BEGIN(INITIAL);
    if (!strlen(yyextra->tmp_buf)) {
	yyextra->tmp_buf = PyMem_Resize(yyextra->tmp_buf, char, 4);
	if (!yyextra->tmp_buf) {return T_ERROR; }
        strcpy(yyextra->tmp_buf, "</>");
        yyextra->tmp_attrs = NULL;
        SETLVAL;
        RETURN(T_TEXT);
    }
    LOWER_TMP;
    PYSTRING_TMP(yyextra->tmp_tag);
    CLEAR_BUF(yyextra->tmp_buf);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_TAGSTART>> {
    UPDATE_BUFPOS;
    if (!strlen(yyextra->tmp_buf)) {
	yyextra->tmp_buf = PyMem_Resize(yyextra->tmp_buf, char, 3);
	if (!yyextra->tmp_buf) {return T_ERROR; }
        strcpy(yyextra->tmp_buf, "<>");
        yyextra->tmp_attrs = NULL;
	SETLVAL;
        RETURN(T_TEXT);
    }
    LOWER_TMP;
    PYSTRING_TMP(yyextra->tmp_tag);
    CLEAR_BUF(yyextra->tmp_buf);
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_TAGSTART>. {
    return T_WAIT;
}

  /*********************** SCRIPT ************************/
<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp][Tt]{RX_WHITE_SPACE}*> {
    UPDATE_BUFPOS;
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_SCRIPT);
}

<S_SCRIPT>[^<]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

  /* this is so shitty */
<S_SCRIPT></[^/] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*/[^Ss] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss]/[^Cc] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc]/[^Rr] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr]/[^Ii] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii]/[^Pp] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp]/[^Tt] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT><\/{RX_WHITE_SPACE}*[Ss][Cc][Rr][Ii][Pp][Tt]{RX_WHITE_SPACE}*/[^>] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_SCRIPT>. {
    return T_WAIT;
}

  /*********************** STYLE ************************/
<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll][Ee]{RX_WHITE_SPACE}*> {
    UPDATE_BUFPOS;
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_STYLE);
}

<S_STYLE>[^<]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

  /* this is so shitty */
<S_STYLE></[^/] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*/[^Ss] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss]/[^Tt] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt]/[^Yy] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy]/[^Ll] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll]/[^Ee] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE><\/{RX_WHITE_SPACE}*[Ss][Tt][Yy][Ll][Ee]{RX_WHITE_SPACE}*/[^>] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_STYLE>. {
    return T_WAIT;
}

  /*********************** ATTRS ************************/
<S_ATTR1>{RX_NAME} {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR2);
}

<S_ATTR1,S_ATTR2,S_ATTR3>\/> {
    UPDATE_BUFPOS;
    FLUSH_ATTRS;
    BEGIN(INITIAL);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_ATTR1,S_ATTR2,S_ATTR3>> {
    UPDATE_BUFPOS;
    FLUSH_ATTRS;
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR2>{RX_DATA} {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_ATTR2>{RX_WHITE_SPACE}+ {
    UPDATE_BUFPOS;
    BEGIN(S_ATTR3);
}

<S_ATTR2,S_ATTR3>{RX_WHITE_SPACE}*{RX_EQUAL}{RX_WHITE_SPACE}* {
    UPDATE_BUFPOS;
    LOWER_TMP;
    PYSTRING_TMP(yyextra->tmp_attrname);
    CLEAR_BUF(yyextra->tmp_buf);
    BEGIN(S_ATTR4);
}

<S_ATTR1,S_ATTR2>.|\n {
    /* this also skips whitespace! */
    UPDATE_BUFPOS;
}

<S_ATTR3>{RX_NAME} {
    UPDATE_BUFPOS;
    LOWER_TMP;
    PYSTRING_TMP(yyextra->tmp_attrname);
    CLEAR_BUF(yyextra->tmp_buf);
    if (yyextra->tmp_attrval!=NULL) return T_ERROR;
    Py_INCREF(Py_None);
    yyextra->tmp_attrval = Py_None;
    if (PyDict_SetItem(yyextra->tmp_attrs, yyextra->tmp_attrname, yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR2);
}

<S_ATTR4>\" {
    UPDATE_BUFPOS;
    BEGIN(S_STRING);
}


<S_ATTR4>\' {
    UPDATE_BUFPOS;
    BEGIN(S_APOSSTRING);
}


<S_ATTR4>[^\012 \t\b\r\n>\'\"]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
    BEGIN(S_ATTR5);
}

<S_ATTR4>> {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR4>\/> {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    BEGIN(INITIAL);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_ATTR4>{RX_WHITE_SPACE}+ {
    UPDATE_BUFPOS;
}

<S_ATTR5>[^\012 \t\b\r\n>]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_ATTR5>> {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    SCRIPT_CHECK;
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START);
}

<S_ATTR5>\/> {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    BEGIN(INITIAL);
    SET_ATTR_LVAL;
    RETURN(T_ELEMENT_START_END);
}

<S_ATTR5>{RX_WHITE_SPACE}+ {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    BEGIN(S_ATTR1);
}

<S_APOSSTRING>\' {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    yyextra->tmp_attrval = quote_string(yyextra->tmp_attrval);
    if (!yyextra->tmp_attrval) return T_ERROR;
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrname = yyextra->tmp_attrval = NULL;
    BEGIN(S_ATTR1);
}

<S_APOSSTRING>[^']+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}


<S_STRING>\" {
    UPDATE_BUFPOS;
    PYSTRING_TMP(yyextra->tmp_attrval);
    CLEAR_BUF(yyextra->tmp_buf);
    yyextra->tmp_attrval = quote_string(yyextra->tmp_attrval);
    if (!yyextra->tmp_attrval) { return T_ERROR; }
    if (PyDict_SetItem(yyextra->tmp_attrs,
		       yyextra->tmp_attrname,
		       yyextra->tmp_attrval)==-1) return T_ERROR;
    Py_DECREF(yyextra->tmp_attrname);
    Py_DECREF(yyextra->tmp_attrval);
    yyextra->tmp_attrval = yyextra->tmp_attrname = NULL;
    BEGIN(S_ATTR1);
}

<S_STRING>[^"]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

  /*********************** TAGEND ************************/
<INITIAL><{RX_WHITE_SPACE}*\/{RX_WHITE_SPACE}*/[A-Za-z] {
    UPDATE_BUFPOS;
    BEGIN(S_TAGEND);
}

<S_TAGEND>[^<>\r\n \t\b\012]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
}

<S_TAGEND>> {
    UPDATE_BUFPOS;
    LOWER_TMP;
    SETLVAL;
    BEGIN(INITIAL);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND><{RX_WHITE_SPACE}* {
    UPDATE_BUFPOS;
    LOWER_TMP;
    SETLVAL;
    SET_ERROR("Missing > in end tag.");
    yyextra->tmp_attrs = PyDict_New();
    if (!yyextra->tmp_attrs) return T_ERROR;
    BEGIN(S_TAGSTART);
    RETURN(T_ELEMENT_END);
}

<S_TAGEND>{RX_WHITE_SPACE}+ {
    /* delete whitespace in or around tag names */
    UPDATE_BUFPOS;
}

  /*********************** TEXT ************************/
<INITIAL>[^<]+ {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
    SETLVAL;
    RETURN(T_TEXT);
}

<INITIAL><[^\012 \t\b\r\nA-Za-z!?/] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
    SETLVAL;
    RETURN(T_TEXT);
}

<INITIAL><{RX_WHITE_SPACE}+[^A-Za-z/] {
    UPDATE_BUFPOS;
    APPEND_TO_TMP(yyleng);
    SETLVAL;
    RETURN(T_TEXT);
}

<INITIAL>. {
    return T_WAIT;
}

%%

#undef malloc
#undef realloc
#undef free

int htmllexInit (void** scanner, UserData* data) {
    yylex_init(scanner);
    yyset_extra(data, *scanner);
    return 0;
}

/* prepare scanner for calls to yylex() */
int htmllexStart (void* scanner, UserData* data, const char* s, int slen) {
    /* append s to data buffer and scan those bytes.
     As Flex does not distinguish between '\0' and EOF characters,
     we must replace '\0' with ' '. */
    int len = strlen(data->buf);
    int i;
    data->buf = PyMem_Resize(data->buf, char, len+slen+1);
    if (!data->buf) return -1;
    for (i=0; i<slen; i++) {
	if (s[i]=='\0')
	    data->buf[len+i] = ' ';
	else
            data->buf[len+i] = s[i];
    }
    data->buf[len+slen] = '\0';
    if (len > data->bufpos) {
        int rewind = len - data->bufpos;
	slen += rewind;
	len -= rewind;
    }
    /* reset userdata */
    data->bufpos = len;
    data->exc_type = NULL;
    data->exc_val = NULL;
    data->exc_tb = NULL;
    /*fprintf(stderr, "SCANNING '%s'\n", data->buf+len);*/
    data->lexbuf = yy_scan_bytes(data->buf+len, slen, scanner);
    return 0;
}

/* delete scanned buffer data */
int htmllexStop (void* scanner, UserData* data) {
    yy_delete_buffer(data->lexbuf, scanner);
    if (data->nextpos > 0) {
	int len = strlen(data->buf);
	int i, j;
	for (i=data->nextpos,j=0; i<len; i++,j++) {
            data->buf[j] = data->buf[i];
	}
	data->buf[j] = '\0';
	data->buf = PyMem_Resize(data->buf, char, len-data->nextpos+1);
        data->bufpos -= data->nextpos;
	data->nextpos = 0;
	if (!data->buf) return -1;
    }
    return 0;
}

int htmllexDestroy (void* scanner) {
    yylex_destroy(scanner);
    return 0;
}
