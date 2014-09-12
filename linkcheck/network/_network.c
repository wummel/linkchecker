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

#include "Python.h"
#ifndef _WIN32
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/route.h>
#include <net/if.h>  
#endif

/* Python 2/3 compatibility */
#if PY_MAJOR_VERSION >= 3
  #define MOD_ERROR_VAL NULL
  #define MOD_SUCCESS_VAL(val) val
  #define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
  #define MOD_DEF(ob, name, doc, methods) \
          static struct PyModuleDef moduledef = { \
            PyModuleDef_HEAD_INIT, name, doc, -1, methods, }; \
          ob = PyModule_Create(&moduledef)
#else
  #define MOD_ERROR_VAL
  #define MOD_SUCCESS_VAL(val)
  #define MOD_INIT(name) void init##name(void)
  #define MOD_DEF(ob, name, doc, methods) \
          ob = Py_InitModule3(name, methods, doc)
#endif

/* The struct ifreq size varies on different platforms, so we need
 this helper function to determine the size of it.
 On Windows platforms this function returns zero.
 */
static PyObject* network_ifreq_size (PyObject* self, PyObject* args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    return Py_BuildValue("i", 
#ifdef _WIN32
0
#else
sizeof(struct ifreq)
#endif
    );
}


static PyMethodDef module_functions[] = {
    {"ifreq_size",  network_ifreq_size, METH_VARARGS,
     "Return sizeof(struct ifreq)."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


MOD_INIT(_network) {
    PyObject *m;
    MOD_DEF(m, "_network", "network helper routines", module_functions);
    if (m == NULL) {
        return MOD_ERROR_VAL;
    }
    return MOD_SUCCESS_VAL(m);
}
