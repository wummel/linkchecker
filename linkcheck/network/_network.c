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


static PyMethodDef _functions[] = {
    {"ifreq_size",  network_ifreq_size, METH_VARARGS,
     "Return sizeof(struct ifreq)."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC init_network(void)
{
    (void) Py_InitModule("_network", _functions);
}
