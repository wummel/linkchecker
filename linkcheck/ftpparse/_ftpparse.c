/*
 * _ftpparse wrapper
 *
 * History:
 * 2001-01-19 fl  created
 *
 * Copyright (c) 2002 by Fredrik Lundh.
 *
 * This wrapper module can be used freely, also for commercial
 * purposes.  See ftpparse.c for more information on the under-
 * lying ftpparse library.
 */

#include "Python.h"
#include "ftpparse.h"

/* the fpObject type is a simple wrapper for ftpparse structs */

typedef struct {
    PyObject_HEAD
    PyObject* string;
    struct ftpparse fp;
} ftpparseObject;

staticforward PyTypeObject ftpparse_Type;

static PyObject *
ftpparse_parse(PyObject* self_, PyObject* args)
{
    ftpparseObject* self;
    int ok;

    PyObject* str;
    if (!PyArg_ParseTuple(args, "O!", &PyString_Type, &str))
        return NULL;

    self = PyObject_NEW(ftpparseObject, &ftpparse_Type);
    if (!self)
	return NULL;

    ok = ftpparse(&self->fp, PyString_AS_STRING(str), PyString_GET_SIZE(str));

    if (!ok) {
        PyObject_DEL(self);
        PyErr_SetString(PyExc_ValueError, "cannot find filename");
        return NULL;
    }

    /* the ftpparse structure contains pointers to inside the source
       string, so we better keep a reference to it */
    Py_INCREF(str);
    self->string = str;

    return (PyObject*) self;
}

static void
ftpparse_dealloc(ftpparseObject* self)
{
    Py_XDECREF(self->string);
    PyMem_DEL(self);
}

static PyObject*  
ftpparse_getattr(ftpparseObject* self, char* name)
{
    /* get descriptor attribute */

    if (strcmp(name, "name") == 0)
        /* filename */
	return Py_BuildValue("s#", self->fp.name, self->fp.namelen);

    if (strcmp(name, "size") == 0) {
        /* size, in bytes (use sizetype to check if text/data) */
        if (self->fp.sizetype == FTPPARSE_SIZE_UNKNOWN)
            goto unknown;
        return Py_BuildValue("l", self->fp.size);
    }

    if (strcmp(name, "mtime") == 0) {
        /* modification time (use mtimetype to check local/remote) */
        if (self->fp.mtimetype == FTPPARSE_MTIME_UNKNOWN)
            goto unknown;
        return Py_BuildValue("l", self->fp.mtime);
    }

    if (strcmp(name, "id") == 0) {
        /* unique identifier */
        if (self->fp.idtype == FTPPARSE_ID_UNKNOWN)
            goto unknown;
	return Py_BuildValue("s#", self->fp.id, self->fp.idlen);
    }

    if (strcmp(name, "tryretr") == 0) {
        PyObject* flag = (self->fp.flagtryretr) ? Py_True : Py_False;
        Py_INCREF(flag);
        return flag;
    }

    if (strcmp(name, "trycwd") == 0) {
        PyObject* flag = (self->fp.flagtrycwd) ? Py_True : Py_False;
        Py_INCREF(flag);
        return flag;
    }

    /* FIXME: what about sizetype, mtimetype, idtype?  return as
       integers or strings?  or use a flag tuple instead of individual
       flags?  */

    PyErr_SetString(PyExc_AttributeError, name);
    return NULL;

  unknown:
    Py_INCREF(Py_None);
    return Py_None;
}

static PyTypeObject ftpparse_Type = {
    PyObject_HEAD_INIT(NULL)
    0, "ftpparse", sizeof(ftpparseObject), 0,
    /* methods */
    (destructor) ftpparse_dealloc, /*tp_dealloc*/
    0, /*tp_print*/
    (getattrfunc) ftpparse_getattr, /*tp_getattr*/
};

static PyMethodDef _functions[] = {
    {"parse", ftpparse_parse, METH_VARARGS},
    {NULL, NULL}
};

PyMODINIT_FUNC
init_ftpparse(void)
{
    ftpparse_Type.ob_type = &PyType_Type;

    Py_InitModule("_ftpparse", _functions);
}
