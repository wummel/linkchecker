#ifndef HTMLSAX_H
#define HTMLSAX_H

#include "Python.h"

/* require Python >= 2.0 */
#ifndef PY_VERSION_HEX
#error please install Python >= 2.0
#endif

#if PY_VERSION_HEX < 0x02000000
#error please install Python >= 2.0
#endif

/* user_data type for SAX calls */
typedef struct {
    /* the Python SAX class instance to issue callbacks */
    PyObject* handler;
    /* Buffer to store still-to-be-scanned characters. After recognizing
     * a complete syntax element, all data up to bufpos will be removed.
     * Before scanning you should append new data to this buffer.
     */
    char* buf;
    /* current position in the buffer counting from zero */
    int bufpos;
    /* current position of next syntax element */
    int nextpos;
    /* temporary vars */
    void* lexbuf;
    char* tmp_buf;
    PyObject* tmp_tag;
    PyObject* tmp_attrname;
    PyObject* tmp_attrval;
    PyObject* tmp_attrs;
    /* stored Python exception (if error occurred in scanner) */
    PyObject* exc_type;
    PyObject* exc_val;
    PyObject* exc_tb;
    /* error string */
    char* error;
} UserData;
extern char* stpcpy(char* src, const char* dest);

#endif
