#ifndef HTMLSAX_H
#define HTMLSAX_H

#include "Python.h"

/* require Python >= 2.3 */
#ifndef PY_VERSION_HEX
#error please install Python >= 2.3
#endif

#if PY_VERSION_HEX < 0x02030000
#error please install Python >= 2.3
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
    unsigned int bufpos;
    /* current position of next syntax element */
    unsigned int nextpos;
    /* position in the stream of data already seen, counting from zero */
    unsigned int pos;
    /* line counter, counting from one */
    unsigned int lineno;
    /* last value of line counter */
    unsigned int last_lineno;
    /* column counter, counting from zero */
    unsigned int column;
    /* last value of column counter */
    unsigned int last_column;
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
    PyObject* error;
} UserData;

#endif
