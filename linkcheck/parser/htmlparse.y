/* the beginning */
%{
/* SAX parser, optimized for WebCleaner */
#include "htmlsax.h"
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

/* resize buf to an empty string */
#define RESIZE_BUF(buf) \
    buf = PyMem_Resize(buf, char, 1); \
    if (buf==NULL) return NULL; \
    buf[0] = '\0'

/* set buf to an empty string */
#define NEW_BUF(buf) \
    buf = PyMem_New(char, 1); \
    if (buf==NULL) return NULL; \
    buf[0] = '\0'

/* call error handler if error object is not NULL */
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
    /* $1 is a tuple (<tag>, <attrs>); <attrs> is a dictionary */
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
    /* $1 is a tuple (<tag>, <attrs>); <attrs> is a dictionary */
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
    CHECK_ERROR(ud, finish_start);
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

/* create parser */
static PyObject* htmlsax_parser_new(PyObject* self, PyObject* args) {
    PyObject* handler;
    parser_object* p;
    if (!PyArg_ParseTuple(args, "O", &handler)) {
	PyErr_SetString(PyExc_TypeError, "SAX2 handler object arg required");
	return NULL;
    }
    p = PyObject_New(parser_object, &parser_type);
    if (!p) {
	PyErr_SetString(PyExc_TypeError, "Allocating parser object failed");
	return NULL;
    }
    Py_INCREF(handler);
    /* reset userData */
    p->userData = PyMem_New(UserData, sizeof(UserData));
    p->userData->handler = handler;
    NEW_BUF(p->userData->buf);
    p->userData->nextpos =
	p->userData->bufpos =
	p->userData->pos =
	p->userData->pos = 0;
    p->userData->column =
	p->userData->last_column =
	p->userData->lineno =
	p->userData->last_lineno = 1;
    NEW_BUF(p->userData->tmp_buf);
    p->userData->tmp_tag = p->userData->tmp_attrname =
	p->userData->tmp_attrval = p->userData->tmp_attrs =
	p->userData->lexbuf = NULL;
    p->userData->exc_type = NULL;
    p->userData->exc_val = NULL;
    p->userData->exc_tb = NULL;
    p->userData->error = NULL;
    p->scanner = NULL;
    htmllexInit(&(p->scanner), p->userData);
    return (PyObject*) p;
}


static void parser_dealloc (PyObject* self) {
    parser_object* p = (parser_object*)self;
    htmllexDestroy(p->scanner);
    Py_DECREF(p->userData->handler);
    PyMem_Del(p->userData->buf);
    PyMem_Del(p->userData->tmp_buf);
    PyMem_Del(p->userData);
    PyMem_DEL(p);
}


/* flush parser buffers, isueing any remaining data as character data */
static PyObject* parser_flush (PyObject* self, PyObject* args) {
    int res=0;
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    /* reset parser variables */
    RESIZE_BUF(p->userData->tmp_buf);
    Py_XDECREF(p->userData->tmp_tag);
    Py_XDECREF(p->userData->tmp_attrs);
    Py_XDECREF(p->userData->tmp_attrval);
    Py_XDECREF(p->userData->tmp_attrname);
    p->userData->tmp_tag = p->userData->tmp_attrs =
	p->userData->tmp_attrval = p->userData->tmp_attrname = NULL;
    p->userData->bufpos = 0;
    if (strlen(p->userData->buf)) {
        // XXX set line, col
        int error = 0;
	PyObject* s = PyString_FromString(p->userData->buf);
	PyObject* callback = NULL;
	PyObject* result = NULL;
	/* reset buffer */
	RESIZE_BUF(p->userData->buf);
	if (s==NULL) { error=1; goto finish_flush; }
	if (PyObject_HasAttrString(p->userData->handler, "characters")==1) {
	    callback = PyObject_GetAttrString(p->userData->handler, "characters");
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
    return Py_BuildValue("i", res);
}


/* return the current parser line number */
static PyObject* parser_lineno (PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    return Py_BuildValue("i", p->userData->lineno);
}


/* return the last parser line number */
static PyObject* parser_last_lineno (PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    return Py_BuildValue("i", p->userData->last_lineno);
}


/* return the current parser column number */
static PyObject* parser_column (PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    return Py_BuildValue("i", p->userData->column);
}


/* return the last parser column number */
static PyObject* parser_last_column (PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    return Py_BuildValue("i", p->userData->last_column);
}


static PyObject* parser_pos (PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    parser_object* p = (parser_object*)self;
    return Py_BuildValue("i", p->userData->pos);
}


/* feed a chunk of data to the parser */
static PyObject* parser_feed(PyObject* self, PyObject* args) {
    /* set up the parse string */
    int slen = 0;
    char* s = NULL;
    if (!PyArg_ParseTuple(args, "t#", &s, &slen)) {
	PyErr_SetString(PyExc_TypeError, "string arg required");
	return NULL;
    }
    /* parse */
    parser_object* p = (parser_object*)self;
    if (htmllexStart(p->scanner, p->userData, s, slen)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not start scanner");
 	return NULL;
    }
    if (yyparse(p->scanner)!=0) {
        if (p->userData->exc_type!=NULL) {
            /* note: we give away these objects, so don't decref */
            PyErr_Restore(p->userData->exc_type,
        		  p->userData->exc_val,
        		  p->userData->exc_tb);
        }
        htmllexStop(p->scanner, p->userData);
        return NULL;
    }
    if (htmllexStop(p->scanner, p->userData)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not stop scanner");
	return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
}


/* reset the parser. This will erase all buffered data! */
static PyObject* parser_reset(PyObject* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
	return NULL;
    }
    parser_object* p = (parser_object*)self;
    if (htmllexDestroy(p->scanner)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not destroy scanner data");
        return NULL;
    }
    /* reset buffer */
    RESIZE_BUF(p->userData->buf);
    RESIZE_BUF(p->userData->tmp_buf);
    p->userData->bufpos =
	p->userData->pos =
	p->userData->nextpos = 0;
    p->userData->column =
	p->userData->last_column =
	p->userData->lineno =
	p->userData->last_lineno = 1;
    p->userData->tmp_tag = p->userData->tmp_attrs =
        p->userData->tmp_attrval = p->userData->tmp_attrname = NULL;
    p->scanner = NULL;
    if (htmllexInit(&(p->scanner), p->userData)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not initialize scanner data");
        return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
}


/* set the debug level, if its >0, debugging is on, =0 means off */
static PyObject* parser_debug(PyObject* self, PyObject* args) {
    int debug;
    if (!PyArg_ParseTuple(args, "i", &debug)) {
        return NULL;
    }
    yydebug = debug;
    parser_object* p = (parser_object*)self;
    debug = htmllexDebug(&(p->scanner), debug);
    return PyInt_FromLong((long)debug);
}


/* type interface */
static PyMethodDef parser_methods[] = {
    {"feed",  parser_feed, METH_VARARGS, "feed data to parse incremental"},
    {"reset", parser_reset, METH_VARARGS, "reset the parser (no flushing)"},
    {"flush", parser_flush, METH_VARARGS, "flush parser buffers"},
    {"debug", parser_debug, METH_VARARGS, "set debug level"},
    {"lineno", parser_lineno, METH_VARARGS, "get the current line number"},
    {"last_lineno", parser_last_lineno, METH_VARARGS, "get the last line number"},
    {"column", parser_column, METH_VARARGS, "get the current column"},
    {"last_column", parser_last_column, METH_VARARGS, "get the last column"},
    {"pos", parser_pos, METH_VARARGS, "get the current scanner position"},
    {NULL, NULL}
};


static PyObject* parser_getattr(PyObject* self, char* name) {
    return Py_FindMethod(parser_methods, self, name);
}


statichere PyTypeObject parser_type = {
    PyObject_HEAD_INIT(NULL)
    0, /* ob_size */
    "parser", /* tp_name */
    sizeof(parser_object), /* tp_size */
    0, /* tp_itemsize */
    /* methods */
    (destructor)parser_dealloc, /* tp_dealloc */
    0, /* tp_print */
    (getattrfunc)parser_getattr, /* tp_getattr */
    0 /* tp_setattr */
};


/* python module interface */
static PyMethodDef htmlsax_methods[] = {
    {"parser", htmlsax_parser_new, METH_VARARGS,
     "Create a new HTML parser object."},
    {NULL, NULL}
};


/* initialization of the htmlsaxhtmlop module */
void inithtmlsax(void) {
    Py_InitModule("htmlsax", htmlsax_methods);
}
