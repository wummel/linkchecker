%{
/* Copyright (C) 2000-2004  Bastian Kleineidam

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
/* Python module definition of a SAX html parser */
#include "htmlsax.h"
#include "structmember.h"
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
extern void* yyget_extra(void*);
extern int yyget_lineno(void*);
#define YYERROR_VERBOSE 1

/* standard error reporting, indicating an internal error */
static int yyerror (char* msg) {
    fprintf(stderr, "htmlsax: internal parse error: %s\n", msg);
    return 0;
}

/* parser.resolve_entities */
static PyObject* resolve_entities;
static PyObject* sorted_dict;

/* macros for easier scanner state manipulation */

/* test whether tag does not need an HTML end tag */
#define NO_HTML_END_TAG(tag) !(strcmp(tag, "area")==0 || \
    strcmp(tag, "base")==0 || \
    strcmp(tag, "basefont")==0 || \
    strcmp(tag, "br")==0 || \
    strcmp(tag, "col")==0 || \
    strcmp(tag, "frame")==0 || \
    strcmp(tag, "hr")==0 || \
    strcmp(tag, "img")==0 || \
    strcmp(tag, "input")==0 || \
    strcmp(tag, "isindex")==0 || \
    strcmp(tag, "link")==0 || \
    strcmp(tag, "meta")==0 || \
    strcmp(tag, "param")==0)

/* clear buffer b, returning NULL on error */
#define CLEAR_BUF(b) \
    b = PyMem_Resize(b, char, 1); \
    if (b==NULL) return NULL; \
    (b)[0] = '\0'

/* clear buffer b, returning NULL and decref self on error */
#define CLEAR_BUF_DECREF(self, b) \
    b = PyMem_Resize(b, char, 1); \
    if (b==NULL) { Py_DECREF(self); return NULL; } \
    (b)[0] = '\0'

#define CHECK_ERROR(ud, label) \
    if (ud->error && PyObject_HasAttrString(ud->handler, "error")==1) { \
	callback = PyObject_GetAttrString(ud->handler, "error"); \
	if (!callback) { error=1; goto label; } \
	result = PyObject_CallFunction(callback, "O", ud->error); \
	if (!result) { error=1; goto label; } \
    }

/* generic callback macro */
#define CALLBACK(ud, attr, format, arg, label) \
    if (PyObject_HasAttrString(ud->handler, attr)==1) { \
	callback = PyObject_GetAttrString(ud->handler, attr); \
	if (callback==NULL) { error=1; goto label; } \
	result = PyObject_CallFunction(callback, format, arg); \
	if (result==NULL) { error=1; goto label; } \
	Py_DECREF(callback); \
	Py_DECREF(result); \
        callback=result=NULL; \
    }

/* set old line and column */
#define SET_OLD_LINECOL \
    ud->last_lineno = ud->lineno; \
    ud->last_column = ud->column

/* parser type definition */
typedef struct {
    PyObject_HEAD
    PyObject* handler;
    UserData* userData;
    void* scanner;
} parser_object;

staticforward PyTypeObject parser_type;

/* use Pythons memory management */
#define malloc PyMem_Malloc
#define realloc PyMem_Realloc
#define free PyMem_Free

%}

/* parser options */
%verbose
%debug
%defines
%output="htmlparse.c"
%pure_parser

/* parser tokens */
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

/* the finish_ labels are for error recovery */
%%

elements: element {}
    | elements element {}
    ;

element: T_WAIT { YYACCEPT; /* wait for more lexer input */ }
| T_ERROR
{
    /* an error occured in the scanner, the python exception must be set */
    UserData* ud = yyget_extra(scanner);
    PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
    YYABORT;
}
| T_ELEMENT_START
{
    /* $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyString, <attrs> is a PyDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM($1, 0);
    PyObject* attrs = PyTuple_GET_ITEM($1, 1);
    int error = 0;
    if (!tag || !attrs) { error = 1; goto finish_start; }
    if (PyObject_HasAttrString(ud->handler, "startElement")==1) {
	callback = PyObject_GetAttrString(ud->handler, "startElement");
	if (!callback) { error=1; goto finish_start; }
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	if (!result) { error=1; goto finish_start; }
	Py_DECREF(callback);
        Py_DECREF(result);
        callback=result=NULL;
    }
    CHECK_ERROR(ud, finish_start);
finish_start:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyString, <attrs> is a PyDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM($1, 0);
    PyObject* attrs = PyTuple_GET_ITEM($1, 1);
    int error = 0;
    char* tagname;
    if (!tag || !attrs) { error = 1; goto finish_start_end; }
    if (PyObject_HasAttrString(ud->handler, "startElement")==1) {
	callback = PyObject_GetAttrString(ud->handler, "startElement");
	if (!callback) { error=1; goto finish_start_end; }
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	if (!result) { error=1; goto finish_start_end; }
	Py_DECREF(callback);
        Py_DECREF(result);
        callback=result=NULL;
    }
    tagname = PyString_AS_STRING(tag);
    if (PyObject_HasAttrString(ud->handler, "endElement")==1 &&
	NO_HTML_END_TAG(tagname)) {
	callback = PyObject_GetAttrString(ud->handler, "endElement");
	if (callback==NULL) { error=1; goto finish_start_end; }
	result = PyObject_CallFunction(callback, "O", tag);
	if (result==NULL) { error=1; goto finish_start_end; }
	Py_DECREF(callback);
        Py_DECREF(result);
        callback=result=NULL;
    }
    CHECK_ERROR(ud, finish_start_end);
finish_start_end:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    char* tagname = PyString_AS_STRING($1);
    if (PyObject_HasAttrString(ud->handler, "endElement")==1 &&
	NO_HTML_END_TAG(tagname)) {
	callback = PyObject_GetAttrString(ud->handler, "endElement");
	if (callback==NULL) { error=1; goto finish_end; }
	result = PyObject_CallFunction(callback, "O", $1);
	if (result==NULL) { error=1; goto finish_end; }
	Py_DECREF(callback);
	Py_DECREF(result);
        callback=result=NULL;
    }
    CHECK_ERROR(ud, finish_end);
finish_end:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "comment", "O", $1, finish_comment);
    CHECK_ERROR(ud, finish_comment);
finish_comment:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "pi", "O", $1, finish_pi);
    CHECK_ERROR(ud, finish_pi);
finish_pi:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "cdata", "O", $1, finish_cdata);
    CHECK_ERROR(ud, finish_cdata);
finish_cdata:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "doctype", "O", $1, finish_doctype);
    CHECK_ERROR(ud, finish_doctype);
finish_doctype:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", $1, finish_script);
    CALLBACK(ud, "endElement", "s", "script", finish_script);
    CHECK_ERROR(ud, finish_script);
finish_script:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
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
    /* $1 is a PyString */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", $1, finish_style);
    CALLBACK(ud, "endElement", "s", "style", finish_style);
    CHECK_ERROR(ud, finish_style);
finish_style:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
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
    /* $1 is a PyString */
    /* Remember this is also called as a lexer error fallback */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", $1, finish_characters);
    CHECK_ERROR(ud, finish_characters);
finish_characters:
    Py_XDECREF(ud->error);
    ud->error = NULL;
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

/* disable python memory interface */
#undef malloc
#undef realloc
#undef free

/* create parser object */
static PyObject* parser_new (PyTypeObject* type, PyObject* args, PyObject* kwds) {
    parser_object* self;
    if ((self = (parser_object*) type->tp_alloc(type, 0)) == NULL)
    {
        return NULL;
    }
    Py_INCREF(Py_None);
    self->handler = Py_None;
    /* reset userData */
    self->userData = PyMem_New(UserData, sizeof(UserData));
    if (self->userData == NULL)
    {
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
    self->userData->sorted_dict = sorted_dict;
    self->userData->exc_type = NULL;
    self->userData->exc_val = NULL;
    self->userData->exc_tb = NULL;
    self->userData->error = NULL;
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0)
    {
        Py_DECREF(self);
        return NULL;
    }
    return (PyObject*) self;
}


/* initialize parser object */
static int parser_init (parser_object* self, PyObject* args, PyObject* kwds) {
    PyObject* handler = NULL;
    static char *kwlist[] = {"handler", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &handler)) {
        return -1;
    }
    if (handler==NULL) {
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
    if (visit(self->handler, arg) < 0) {
        return -1;
    }
    return 0;
}


/* clear all used subobjects participating in reference cycles */
static int parser_clear (parser_object* self) {
    Py_XDECREF(self->handler);
    self->handler = NULL;
    self->userData->handler = NULL;
    return 0;
}


/* free all allocated resources of parser object */
static void parser_dealloc (parser_object* self) {
    htmllexDestroy(self->scanner);
    parser_clear(self);
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
    Py_XDECREF(self->userData->tmp_tag);
    Py_XDECREF(self->userData->tmp_attrs);
    Py_XDECREF(self->userData->tmp_attrval);
    Py_XDECREF(self->userData->tmp_attrname);
    self->userData->tmp_tag = self->userData->tmp_attrs =
	self->userData->tmp_attrval = self->userData->tmp_attrname = NULL;
    self->userData->bufpos = 0;
    if (strlen(self->userData->buf)) {
        /* XXX set line, col */
        int error = 0;
	PyObject* s = PyString_FromString(self->userData->buf);
	PyObject* callback = NULL;
	PyObject* result = NULL;
	/* reset buffer */
	CLEAR_BUF(self->userData->buf);
	if (s==NULL) { error=1; goto finish_flush; }
	if (PyObject_HasAttrString(self->handler, "characters")==1) {
	    callback = PyObject_GetAttrString(self->handler, "characters");
	    if (callback==NULL) { error=1; goto finish_flush; }
	    result = PyObject_CallFunction(callback, "O", s);
	    if (result==NULL) { error=1; goto finish_flush; }
	}
    finish_flush:
	Py_XDECREF(callback);
	Py_XDECREF(result);
	Py_XDECREF(s);
	if (error==1) {
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


static PyObject* parser_gethandler (parser_object* self, void* closure) {
    Py_INCREF(self->handler);
    return self->handler;
}

static int parser_sethandler (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
       PyErr_SetString(PyExc_TypeError, "Cannot delete parser handler");
       return -1;
    }
    Py_DECREF(self->handler);
    Py_INCREF(value);
    self->handler = value;
    self->userData->handler = self->handler;
    return 0;
}

/* type interface */

static PyMemberDef parser_members[] = {
    {NULL}  /* Sentinel */
};

static PyGetSetDef parser_getset[] = {
    {"handler", (getter)parser_gethandler, (setter)parser_sethandler,
     "handler object", NULL},
    {NULL}  /* Sentinel */
};

static PyMethodDef parser_methods[] = {
    {"feed",  (PyCFunction)parser_feed, METH_VARARGS, "feed data to parse incremental"},
    {"reset", (PyCFunction)parser_reset, METH_VARARGS, "reset the parser (no flushing)"},
    {"flush", (PyCFunction)parser_flush, METH_VARARGS, "flush parser buffers"},
    {"debug", (PyCFunction)parser_debug, METH_VARARGS, "set debug level"},
    {"lineno",      (PyCFunction)parser_lineno,      METH_VARARGS, "get the current line number"},
    {"last_lineno", (PyCFunction)parser_last_lineno, METH_VARARGS, "get the last line number"},
    {"column",      (PyCFunction)parser_column,      METH_VARARGS, "get the current column"},
    {"last_column", (PyCFunction)parser_last_column, METH_VARARGS, "get the last column"},
    {"pos",         (PyCFunction)parser_pos,         METH_VARARGS, "get the current scanner position"},
    {NULL} /* Sentinel */
};


static PyTypeObject parser_type = {
    PyObject_HEAD_INIT(NULL)
    0,              /* ob_size */
    "htmlsax.parser",      /* tp_name */
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
};


/* python module interface 
     "Create a new HTML parser object with handler (which may be None).\n"
     "\n"
     "Used callbacks (they don't have to be defined) of a handler are:\n"
     "comment(data): <!--data-->\n"
     "startElement(tag, attrs): <tag {attr1:value1,attr2:value2,..}>\n"
     "endElement(tag): </tag>\n"
     "doctype(data): <!DOCTYPE data?>\n"
     "pi(name, data=None): <?name data?>\n"
     "cdata(data): <![CDATA[data]]>\n"
     "characters(data): data\n"
     "\n"
     "Additionally, there are error and warning callbacks:\n"
     "error(msg)\n"
     "warning(msg)\n"
     "fatalError(msg)\n"},

*/

static PyMethodDef htmlsax_methods[] = {
    {NULL} /* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
/* initialization of the htmlsax module */
PyMODINIT_FUNC inithtmlsax (void) {
    PyObject* m;
    if (PyType_Ready(&parser_type) < 0) {
        return;
    }
    if ((m = Py_InitModule3("htmlsax", htmlsax_methods, "SAX HTML parser routines"))==NULL) {
        return;
    }
    Py_INCREF(&parser_type);
    if (PyModule_AddObject(m, "parser", (PyObject *)&parser_type)==-1) {
        /* init error */
        PyErr_Print();
    }
    if ((m = PyImport_ImportModule("wc.parser"))==NULL) {
        return;
    }
    if ((resolve_entities = PyObject_GetAttrString(m, "resolve_entities"))==NULL) {
        return;
    }
    if ((sorted_dict = PyObject_GetAttrString(m, "SortedDict"))==NULL) {
        return;
    }
}
