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
/*
 Includes header definitions for the HTML Sax parser Python module.
 */
#ifndef HTMLSAX_H
#define HTMLSAX_H

#include "Python.h"

/* require Python >= 2.6 */
#ifndef PY_VERSION_HEX
#error please install Python >= 2.6
#endif

#if PY_VERSION_HEX < 0x02060000
#error please install Python >= 2.6
#endif

/* user_data type for SAX calls */
typedef struct {
    /* the Python SAX object to issue callbacks */
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
    /* column counter, counting from zero */
    unsigned int column;
    /* value of line counter before the current token */
    unsigned int last_lineno;
    /* value of column counter before the current token */
    unsigned int last_column;
    /* input buffer of lexer, must be deleted when the parsing stops */
    void* lexbuf;
    /* temporary character buffer */
    char* tmp_buf;
    /* temporary HTML start or end tag name */
    PyObject* tmp_tag;
    /* temporary HTML start tag attribute name */
    PyObject* tmp_attrname;
    /* temporary HTML start tag attribute value */
    PyObject* tmp_attrval;
    /* temporary HTML start tag attribute list (a SortedDict) */
    PyObject* tmp_attrs;
    /* HtmlParser.resolve_entities */
    PyObject* resolve_entities;
    /* HtmlParser.SortedDict */
    PyObject* list_dict;
    /* stored Python exception (if error occurred in scanner) */
    PyObject* exc_type;
    PyObject* exc_val;
    PyObject* exc_tb;
    /* the parser object itself */
    PyObject* parser;
} UserData;

#endif
