%{
/* Copyright (C) 2000-2014 Bastian Kleineidam

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/
/* A SAX HTML parser. Includes Python module definition to make it
   usable for Python programs.
*/
#include "htmlsax.h"      /* SAX interface (includes Python.h) */
#include "structmember.h" /* Python include for object definition */
#include <string.h>
#include <stdio.h>

/* bison type definitions */
#define YYSTYPE PyObject*
#define YYPARSE_PARAM scanner
#define YYLEX_PARAM scanner
/* extern functions found in htmllex.l */
extern int yylex(YYSTYPE* yylvalp, void* scanner);
extern int htmllexInit (void** scanner, UserData* data);
extern int htmllexDebug (void** scanner, int debug);
extern int htmllexStart (void* scanner, UserData* data, const char* s, int slen);
extern int htmllexStop (void* scanner, UserData* data);
extern int htmllexDestroy (void* scanner);
extern UserData* yyget_extra(void* scanner);
extern int yyget_lineno(void*);
#define YYERROR_VERBOSE 1

/* standard error reporting, indicating an internal error */
static int yyerror (char* msg) {
    fprintf(stderr, "htmlsax: internal parse error: %s\n", msg);
    return 0;
}

/* existing Python methods */

/* parser.resolve_entities */
static PyObject* resolve_entities;
/* ListDict class, sorted dictionary */
static PyObject* list_dict;
/* set_encoding helper function */
static PyObject* set_encoding;
/* set_doctype helper function */
static PyObject* set_doctype;
/* the unicode string u'meta' */
static PyObject* u_meta;

/* macros for easier scanner state manipulation */

/* clear buffer b, returning NULL on error */
#define CLEAR_BUF(b) \
    b = PyMem_Resize(b, char, 1); \
    if (b == NULL) return NULL; \
    (b)[0] = '\0'

/* clear buffer b, returning NULL and decref self on error */
#define CLEAR_BUF_DECREF(self, b) \
    b = PyMem_Resize(b, char, 1); \
    if (b == NULL) { Py_DECREF(self); return NULL; } \
    (b)[0] = '\0'

/* check an error condition and if true set error flag and goto given label */
#define CHECK_ERROR(cond, label) \
    if (cond) { \
        error = 1; \
        goto label; \
    }

/* generic Python callback macro */
#define CALLBACK(ud, attr, format, arg, label) \
    if (PyObject_HasAttrString(ud->handler, attr) == 1) { \
	callback = PyObject_GetAttrString(ud->handler, attr); \
	CHECK_ERROR((callback == NULL), label); \
	result = PyObject_CallFunction(callback, format, arg); \
	CHECK_ERROR((result == NULL), label); \
	Py_CLEAR(callback); \
	Py_CLEAR(result); \
    }

/* set old line and column */
#define SET_OLD_LINECOL \
    ud->last_lineno = ud->lineno; \
    ud->last_column = ud->column

/* parser type definition */
typedef struct {
    PyObject_HEAD
    /* the handler object */
    PyObject* handler;
    /* the charset encoding (PyStringObject) */
    PyObject* encoding;
    /* the document type (PyStringObject) */
    PyObject* doctype;
    UserData* userData;
    void* scanner;
} parser_object;

/* use Pythons memory management */
#define YYMALLOC PyMem_Malloc
#define YYFREE PyMem_Free

/* Test whether tag does not need an HTML end tag.
   @ptag: ASCII encoded Python string in lowercase (!)
   @parser: SAX parser object
   @return: < 0 on error, > 0 if HTML end tag is needed, else 0
*/
static int html_end_tag (PyObject* ptag, PyObject* parser) {
    PyObject* pdoctype = NULL;
    char* doctype;
    int error = 0;
    int ret = 1;
    pdoctype = PyObject_GetAttrString(parser, "doctype");
    CHECK_ERROR((pdoctype == NULL), finish_html_end_tag);
    doctype = PyString_AsString(pdoctype);
    CHECK_ERROR((doctype == NULL), finish_html_end_tag);
    /* check for HTML (else it's presumably XHTML) */
    if (strcmp(doctype, "HTML") == 0) {
        char* tag = PyString_AsString(ptag);
        CHECK_ERROR((tag == NULL), finish_html_end_tag);
        ret = strcmp(tag, "area")!=0 &&
            strcmp(tag, "base")!=0 &&
            strcmp(tag, "basefont")!=0 &&
            strcmp(tag, "br")!=0 &&
            strcmp(tag, "col")!=0 &&
            strcmp(tag, "frame")!=0 &&
            strcmp(tag, "hr")!=0 &&
            strcmp(tag, "img")!=0 &&
            strcmp(tag, "input")!=0 &&
            strcmp(tag, "isindex")!=0 &&
            strcmp(tag, "link")!=0 &&
            strcmp(tag, "meta")!=0 &&
            strcmp(tag, "param")!=0;
    }
finish_html_end_tag:
    Py_XDECREF(pdoctype);
    if (error) {
        return -1;
    }
    return ret;
}

%}

/* parser options */
%verbose
%debug
%defines
%output="htmlparse.c"
%pure_parser

/* parser tokens, see below for what they mean */
%token T_WAIT
%token T_ERROR
%token T_TEXT
%token T_ELEMENT_START
%token T_ELEMENT_START_END
%token T_ELEMENT_END
%token T_SCRIPT
%token T_STYLE
%token T_PI
%token T_COMMENT
%token T_CDATA
%token T_DOCTYPE

/* note: the finish_ labels are for error recovery */
%%

elements: element {
    /* parse a single element */
}
| elements element {
    /* parse a list of elements */
}
;

element: T_WAIT {
    /* wait for more lexer input */
    YYACCEPT;
}
| T_ERROR
{
    /* an error occured in the scanner, the python exception must be set */
    UserData* ud = yyget_extra(scanner);
    PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
    YYABORT;
}
| T_ELEMENT_START
{
    /* parsed HTML start tag (eg. <a href="blubb">)
       $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a ListDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM($1, 0);
    PyObject* attrs = PyTuple_GET_ITEM($1, 1);
    int error = 0;
    int cmp;
    CHECK_ERROR((tag == NULL || attrs == NULL), finish_start);
    cmp = PyObject_RichCompareBool(tag, u_meta, Py_EQ);
    CHECK_ERROR((cmp == -1), finish_start);
    if (cmp == 1) {
        /* set encoding */
        result = PyObject_CallFunction(set_encoding, "OO", ud->parser, attrs);
        CHECK_ERROR((result == NULL), finish_start);
        Py_CLEAR(result);
    }
    if (PyObject_HasAttrString(ud->handler, "start_element") == 1) {
	callback = PyObject_GetAttrString(ud->handler, "start_element");
	CHECK_ERROR((!callback), finish_start);
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	CHECK_ERROR((!result), finish_start);
	Py_CLEAR(callback);
        Py_CLEAR(result);
    }
finish_start:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_ELEMENT_START_END
{
    /* parsed HTML start-end tag (eg. <br/>)
       $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a ListDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM($1, 0);
    PyObject* attrs = PyTuple_GET_ITEM($1, 1);
    int error = 0;
    int cmp;
    char* fname;
    PyObject* tagname;
    CHECK_ERROR((tag == NULL || attrs == NULL), finish_start_end);
    tagname = PyUnicode_AsEncodedString(tag, "ascii", "ignore");
    CHECK_ERROR((tagname == NULL), finish_start_end);
    cmp = PyObject_RichCompareBool(tag, u_meta, Py_EQ);
    CHECK_ERROR((cmp == -1), finish_start_end);
    if (cmp == 1) {
        /* set encoding */
        result = PyObject_CallFunction(set_encoding, "OO", ud->parser, attrs);
        CHECK_ERROR((result == NULL), finish_start_end);
        Py_CLEAR(result);
    }
    cmp = html_end_tag(tagname, ud->parser);
    CHECK_ERROR((cmp < 0), finish_start_end);
    fname = (cmp == 0 ? "start_element" : "start_end_element");
    if (PyObject_HasAttrString(ud->handler, fname) == 1) {
	callback = PyObject_GetAttrString(ud->handler, fname);
	CHECK_ERROR((!callback), finish_start_end);
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	CHECK_ERROR((!result), finish_start_end);
	Py_CLEAR(callback);
        Py_CLEAR(result);
    }
finish_start_end:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_ELEMENT_END
{
    /* parsed HTML end tag (eg. </b>)
       $1 is a PyUnicode with the tag name */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    int cmp;
    /* encode tagname in ASCII, ignoring any unknown chars */
    PyObject* tagname = PyUnicode_AsEncodedString($1, "ascii", "ignore");
    if (tagname == NULL) {
        error = 1;
        goto finish_end;
    }
    cmp = html_end_tag(tagname, ud->parser);
    CHECK_ERROR((cmp < 0), finish_end);
    if (PyObject_HasAttrString(ud->handler, "end_element") == 1 && cmp > 0) {
	callback = PyObject_GetAttrString(ud->handler, "end_element");
	CHECK_ERROR((callback == NULL), finish_end);
	result = PyObject_CallFunction(callback, "O", $1);
	CHECK_ERROR((result == NULL), finish_end);
	Py_CLEAR(callback);
	Py_CLEAR(result);
    }
finish_end:
    Py_XDECREF(tagname);
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_COMMENT
{
    /* parsed HTML comment (eg. <!-- bla -->)
       $1 is a PyUnicode with the comment content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "comment", "O", $1, finish_comment);
finish_comment:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_PI
{
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "pi", "O", $1, finish_pi);
finish_pi:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_CDATA
{
    /* parsed HTML CDATA (eg. <![CDATA[spam and eggs ...]]>)
       $1 is a PyUnicode with the CDATA content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "cdata", "O", $1, finish_cdata);
finish_cdata:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_DOCTYPE
{
    /* parsed HTML doctype (eg. <!DOCTYPE imadoofus system>)
       $1 is a PyUnicode with the doctype content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    /* set encoding */
    result = PyObject_CallFunction(set_doctype, "OO", ud->parser, $1);
    CHECK_ERROR((result == NULL), finish_doctype);
    Py_CLEAR(result);
    CALLBACK(ud, "doctype", "O", $1, finish_doctype);
finish_doctype:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_SCRIPT
{
    /* parsed HTML script content (plus end tag which is omitted)
       $1 is a PyUnicode with the script content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* script = PyUnicode_DecodeASCII("script", 6, "ignore");
    CHECK_ERROR((script == NULL), finish_script);
    CALLBACK(ud, "characters", "O", $1, finish_script);
    /* emit the omitted end tag */
    CALLBACK(ud, "end_element", "O", script, finish_script);
finish_script:
    Py_XDECREF(callback);
    Py_XDECREF(script);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_STYLE
{
    /* parsed HTML style content (plus end tag which is omitted)
       $1 is a PyUnicode with the style content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* style = PyUnicode_DecodeASCII("style", 5, "ignore");
    CHECK_ERROR((style == NULL), finish_style);
    CALLBACK(ud, "characters", "O", $1, finish_style);
    /* emit the omitted end tag */
    CALLBACK(ud, "end_element", "O", style, finish_style);
finish_style:
    Py_XDECREF(callback);
    Py_XDECREF(style);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
| T_TEXT
{
    /* parsed HTML text data
       $1 is a PyUnicode with the text */
    /* Remember this is also called as a lexer fallback when no
       HTML structure element could be recognized. */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", $1, finish_characters);
finish_characters:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF($1);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
;

%%

/* create parser object */
static PyObject* parser_new (PyTypeObject* type, PyObject* args, PyObject* kwds) {
    parser_object* self;
    if ((self = (parser_object*) type->tp_alloc(type, 0)) == NULL) {
        return NULL;
    }
    Py_INCREF(Py_None);
    self->handler = Py_None;
    /* reset userData */
    self->userData = PyMem_New(UserData, sizeof(UserData));
    if (self->userData == NULL) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->userData->handler = self->handler;
    self->userData->buf = NULL;
    CLEAR_BUF_DECREF(self, self->userData->buf);
    self->userData->nextpos = 0;
    self->userData->bufpos = 0;
    self->userData->pos = 0;
    self->userData->column = 1;
    self->userData->last_column = 1;
    self->userData->lineno = 1;
    self->userData->last_lineno = 1;
    self->userData->tmp_buf = NULL;
    CLEAR_BUF_DECREF(self, self->userData->tmp_buf);
    self->userData->tmp_tag = self->userData->tmp_attrname =
        self->userData->tmp_attrval = self->userData->tmp_attrs =
        self->userData->lexbuf = NULL;
    self->userData->resolve_entities = resolve_entities;
    self->userData->list_dict = list_dict;
    self->userData->exc_type = NULL;
    self->userData->exc_val = NULL;
    self->userData->exc_tb = NULL;
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->encoding = PyString_FromString("iso8859-1");
    if (self->encoding == NULL) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->doctype = PyString_FromString("HTML");
    if (self->doctype == NULL) {
        Py_DECREF(self->encoding);
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->userData->parser = (PyObject*)self;
    return (PyObject*) self;
}


/* initialize parser object */
static int parser_init (parser_object* self, PyObject* args, PyObject* kwds) {
    PyObject* handler = NULL;
    static char *kwlist[] = {"handler", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &handler)) {
        return -1;
    }
    if (handler == NULL) {
        return 0;
    }
    Py_DECREF(self->handler);
    Py_INCREF(handler);
    self->handler = handler;
    self->userData->handler = self->handler;
    return 0;
}


/* traverse all used subobjects participating in reference cycles */
static int parser_traverse (parser_object* self, visitproc visit, void* arg) {
    Py_VISIT(self->handler);
    return 0;
}


/* clear all used subobjects participating in reference cycles */
static int parser_clear (parser_object* self) {
    self->userData->handler = NULL;
    Py_CLEAR(self->handler);
    return 0;
}


/* free all allocated resources of parser object */
static void parser_dealloc (parser_object* self) {
    htmllexDestroy(self->scanner);
    parser_clear(self);
    self->userData->parser = NULL;
    Py_CLEAR(self->encoding);
    Py_CLEAR(self->doctype);
    PyMem_Del(self->userData->buf);
    PyMem_Del(self->userData->tmp_buf);
    PyMem_Del(self->userData);
    self->ob_type->tp_free((PyObject*)self);
}


/* feed a chunk of data to the parser */
static PyObject* parser_feed (parser_object* self, PyObject* args) {
    /* set up the parse string */
    int slen = 0;
    char* s = NULL;
    if (!PyArg_ParseTuple(args, "t#", &s, &slen)) {
	PyErr_SetString(PyExc_TypeError, "string arg required");
	return NULL;
    }
    /* parse */
    if (htmllexStart(self->scanner, self->userData, s, slen)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not start scanner");
 	return NULL;
    }
    if (yyparse(self->scanner)!=0) {
        if (self->userData->exc_type!=NULL) {
            /* note: we give away these objects, so don't decref */
            PyErr_Restore(self->userData->exc_type,
        		  self->userData->exc_val,
        		  self->userData->exc_tb);
        }
        htmllexStop(self->scanner, self->userData);
        return NULL;
    }
    if (htmllexStop(self->scanner, self->userData)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not stop scanner");
	return NULL;
    }
    Py_RETURN_NONE;
}


/* flush all parser buffers */
static PyObject* parser_flush (parser_object* self, PyObject* args) {
    int res = 0;
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    /* reset parser variables */
    CLEAR_BUF(self->userData->tmp_buf);
    Py_CLEAR(self->userData->tmp_tag);
    Py_CLEAR(self->userData->tmp_attrs);
    Py_CLEAR(self->userData->tmp_attrval);
    Py_CLEAR(self->userData->tmp_attrname);
    self->userData->bufpos = 0;
    if (strlen(self->userData->buf)) {
        int error = 0;
        int i;
       	PyObject* callback = NULL;
        PyObject* result = NULL;
        const char* enc;
        PyObject* s;
        /* set line, col */
        for (i=0; i<strlen(self->userData->buf); ++i) {
            if (self->userData->buf[i] == '\n') {
                ++(self->userData->lineno);
                self->userData->column = 1;
            }
            else ++(self->userData->column);
        }
        enc = PyString_AsString(self->encoding);
        s = PyUnicode_Decode(self->userData->buf,
               (Py_ssize_t)strlen(self->userData->buf), enc, "ignore");
        /* reset buffer */
        CLEAR_BUF(self->userData->buf);
        if (s == NULL) { error = 1; goto finish_flush; }
        if (PyObject_HasAttrString(self->handler, "characters") == 1) {
            callback = PyObject_GetAttrString(self->handler, "characters");
            if (callback == NULL) { error = 1; goto finish_flush; }
            result = PyObject_CallFunction(callback, "O", s);
            if (result == NULL) { error = 1; goto finish_flush; }
        }
    finish_flush:
	Py_XDECREF(callback);
	Py_XDECREF(result);
	Py_XDECREF(s);
	if (error == 1) {
	    return NULL;
	}
    }
    if (htmllexDestroy(self->scanner)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not destroy scanner data");
        return NULL;
    }
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not initialize scanner data");
        return NULL;
    }
    return Py_BuildValue("i", res);
}


/* return the current parser line number */
static PyObject* parser_lineno (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->lineno);
}


/* return the last parser line number */
static PyObject* parser_last_lineno (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->last_lineno);
}


/* return the current parser column number */
static PyObject* parser_column (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->column);
}


/* return the last parser column number */
static PyObject* parser_last_column (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->last_column);
}


/* return the parser position in data stream */
static PyObject* parser_pos (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->pos);
}


/* return buffered parser data up to given length */
static PyObject* parser_peek (parser_object* self, PyObject* args) {
    Py_ssize_t len, buflen;
    if (!PyArg_ParseTuple(args, "n", &len)) {
        return NULL;
    }
    if (len < 0) {
	PyErr_SetString(PyExc_TypeError, "peek length must not be negative");
        return NULL;
    }
    buflen = strlen(self->userData->buf);
    if (!buflen || self->userData->bufpos >= buflen) {
        return PyString_FromString("");
    }
    if (self->userData->bufpos + len >= buflen) {
        len = buflen - self->userData->bufpos - 1;
    }
    return PyString_FromStringAndSize(self->userData->buf + self->userData->bufpos, len);
}


/* reset the parser. This will erase all buffered data! */
static PyObject* parser_reset (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
	return NULL;
    }
    if (htmllexDestroy(self->scanner)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not destroy scanner data");
        return NULL;
    }
    /* reset buffer */
    CLEAR_BUF(self->userData->buf);
    CLEAR_BUF(self->userData->tmp_buf);
    self->userData->bufpos =
        self->userData->pos =
        self->userData->nextpos = 0;
    self->userData->column =
	self->userData->last_column =
	self->userData->lineno =
	self->userData->last_lineno = 1;
    self->userData->tmp_tag = self->userData->tmp_attrs =
        self->userData->tmp_attrval = self->userData->tmp_attrname = NULL;
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not initialize scanner data");
        return NULL;
    }
    Py_RETURN_NONE;
}


/* set the debug level, if its >0, debugging is on, =0 means off */
static PyObject* parser_debug (parser_object* self, PyObject* args) {
    int debug;
    if (!PyArg_ParseTuple(args, "i", &debug)) {
        return NULL;
    }
    yydebug = debug;
    debug = htmllexDebug(&(self->scanner), debug);
    return PyInt_FromLong((long)debug);
}


/* get SAX handler object */
static PyObject* parser_gethandler (parser_object* self, void* closure) {
    Py_INCREF(self->handler);
    return self->handler;
}


/* set SAX handler object */
static int parser_sethandler (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
       PyErr_SetString(PyExc_TypeError, "Cannot delete parser handler");
       return -1;
    }
    Py_DECREF(self->handler);
    Py_INCREF(value);
    self->handler = value;
    self->userData->handler = value;
    return 0;
}


/* get parser encoding */
static PyObject* parser_getencoding (parser_object* self, void* closure) {
    Py_INCREF(self->encoding);
    return self->encoding;
}


/* set parser encoding */
static int parser_setencoding (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete encoding");
        return -1;
    }
    if (!PyString_CheckExact(value)) {
        PyErr_SetString(PyExc_TypeError, "encoding must be string");
        return -1;
    }
    Py_DECREF(self->encoding);
    Py_INCREF(value);
    self->encoding = value;
    if (yydebug > 0) {
        /* print debug message */
        PyObject* repr = PyObject_Repr(value);
        if (repr == NULL) {
            return -1;
        }
        fprintf(stderr, "htmlsax: set encoding to %s\n", PyString_AsString(repr));
        Py_DECREF(repr);
    }
    return 0;
}


/* get parser doctype */
static PyObject* parser_getdoctype (parser_object* self, void* closure) {
    Py_INCREF(self->doctype);
    return self->doctype;
}


/* set parser doctype */
static int parser_setdoctype (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete doctype");
        return -1;
    }
    if (!PyString_CheckExact(value)) {
        PyObject* repr = PyObject_Repr(value);
        char* cp = PyString_AsString(repr);
        if (NULL == cp)
            return -1;
        PyErr_Format(PyExc_TypeError, "doctype %s must be string", cp);
        return -1;
    }
    Py_DECREF(self->doctype);
    Py_INCREF(value);
    self->doctype = value;
    return 0;
}


/* type interface */

static PyMemberDef parser_members[] = {
    {NULL}  /* Sentinel */
};

static PyGetSetDef parser_getset[] = {
    {"handler", (getter)parser_gethandler, (setter)parser_sethandler,
     "handler object", NULL},
    {"encoding", (getter)parser_getencoding, (setter)parser_setencoding,
     "encoding", NULL},
    {"doctype", (getter)parser_getdoctype, (setter)parser_setdoctype,
     "doctype", NULL},
    {NULL}  /* Sentinel */
};

static PyMethodDef parser_methods[] = {
    {"feed", (PyCFunction)parser_feed, METH_VARARGS, "feed data to parse incremental"},
    {"reset", (PyCFunction)parser_reset, METH_VARARGS, "reset the parser (no flushing)"},
    {"flush", (PyCFunction)parser_flush, METH_VARARGS, "flush parser buffers"},
    {"debug", (PyCFunction)parser_debug, METH_VARARGS, "set debug level"},
    {"lineno", (PyCFunction)parser_lineno, METH_VARARGS, "get the current line number"},
    {"last_lineno", (PyCFunction)parser_last_lineno, METH_VARARGS, "get the last line number"},
    {"column", (PyCFunction)parser_column, METH_VARARGS, "get the current column"},
    {"last_column", (PyCFunction)parser_last_column, METH_VARARGS, "get the last column"},
    {"pos", (PyCFunction)parser_pos, METH_VARARGS, "get the current scanner position"},
    {"peek", (PyCFunction)parser_peek, METH_VARARGS, "get up to given length of buffered data from current parse position"},
    {NULL} /* Sentinel */
};


static PyTypeObject parser_type = {
    PyObject_HEAD_INIT(NULL)
    0,              /* ob_size */
    "linkcheck.HtmlParser.htmlsax.parser",      /* tp_name */
    sizeof(parser_object), /* tp_size */
    0,              /* tp_itemsize */
    /* methods */
    (destructor)parser_dealloc, /* tp_dealloc */
    0,              /* tp_print */
    0,              /* tp_getattr */
    0,              /* tp_setattr */
    0,              /* tp_compare */
    0,              /* tp_repr */
    0,              /* tp_as_number */
    0,              /* tp_as_sequence */
    0,              /* tp_as_mapping */
    0,              /* tp_hash */
    0,              /* tp_call */
    0,              /* tp_str */
    0,              /* tp_getattro */
    0,              /* tp_setattro */
    0,              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | 
      Py_TPFLAGS_HAVE_GC, /* tp_flags */
    "HTML parser object", /* tp_doc */
    (traverseproc)parser_traverse, /* tp_traverse */
    (inquiry)parser_clear, /* tp_clear */
    0,              /* tp_richcompare */
    0,              /* tp_weaklistoffset */
    0,              /* tp_iter */
    0,              /* tp_iternext */
    parser_methods, /* tp_methods */
    parser_members, /* tp_members */
    parser_getset,  /* tp_getset */
    0,              /* tp_base */
    0,              /* tp_dict */
    0,              /* tp_descr_get */
    0,              /* tp_descr_set */
    0,              /* tp_dictoffset */
    (initproc)parser_init,  /* tp_init */
    0,              /* tp_alloc */
    parser_new,     /* tp_new */
    0,              /* tp_free */
    0,              /* tp_is_gc */
    0,              /* tp_bases */
    0,              /* tp_mro */
    0,              /* tp_cache */
    0,              /* tp_subclasses */
    0,              /* tp_weaklist */
    0,              /* tp_del */
};


static PyMethodDef htmlsax_methods[] = {
    {NULL} /* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
/* initialization of the htmlsax module */
PyMODINIT_FUNC inithtmlsax (void) {
    PyObject* m = NULL;
    if (PyType_Ready(&parser_type) < 0) {
        return;
    }
    if ((m = Py_InitModule3("htmlsax", htmlsax_methods, "SAX HTML parser routines")) == NULL) {
        return;
    }
    Py_INCREF(&parser_type);
    if (PyModule_AddObject(m, "parser", (PyObject*)&parser_type) == -1) {
        /* init error */
        PyErr_Print();
    }
    if ((m = PyImport_ImportModule("linkcheck.HtmlParser")) == NULL) {
        return;
    }
    if ((resolve_entities = PyObject_GetAttrString(m, "resolve_entities")) == NULL) {
        Py_DECREF(m);
        return;
    }
    if ((set_encoding = PyObject_GetAttrString(m, "set_encoding")) == NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(m);
        return;
    }
    if ((set_doctype = PyObject_GetAttrString(m, "set_doctype")) == NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(set_encoding);
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
    if ((u_meta = PyString_Decode("meta", 4, "ascii", "ignore")) == NULL) {
        return;
    }
    if ((m = PyImport_ImportModule("linkcheck.containers")) == NULL) {
        return;
    }
    if ((list_dict = PyObject_GetAttrString(m, "ListDict")) == NULL) {
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
}
