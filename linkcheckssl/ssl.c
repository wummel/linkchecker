/* @(#)ssl.c	1.1 VMS-99/01/30 python wrapper for SSLeay https
 */

#include "Python.h"
#if defined(WITH_THREAD) && !defined(HAVE_GETHOSTBYNAME_R) && !defined(MS_WINDOWS)
#include "thread.h"
#endif

#include <sys/types.h>
#ifndef MS_WINDOWS
#include <sys/socket.h>
#else
#include <winsock.h>
#endif

#if defined(PYOS_OS2)
#define  INCL_DOS
#define  INCL_DOSERRORS
#define  INCL_NOPMAPI
#include <os2.h>
#endif

#include "ssl.h"
#include "err.h"

/* Global variable holding the exception type for errors detected
   by this module (but not argument type or memory errors, etc.). */

static PyObject *PySslError;

typedef struct {
    PyObject_HEAD
    int		sock_fd;
    PyObject 	*x_attr;	/* attributes dictionary */
    SSL_CTX 	*ctx;
    SSL     	*ssl;
    X509    	*server_cert;
    BIO		*sbio;
    char    	server[256];
    char	issuer[256];
} PySslObject;

staticforward PyTypeObject SSL_Type;
#define PySslObject_Check(v)	((v)->ob_type == &SSL_Type)
#define PY_SSL_ERR_MAX 256

/*
 * raise an error according to errno, return NULL
 */
static PyObject* PySsl_errno (void) {
#ifdef MS_WINDOWS
    if (WSAGetLastError()) {
        PyObject *v = Py_BuildValue("(is)",WSAGetLastError(),"winsock error");

        if (v) {
            PyErr_SetObject(PySslError,v);
            Py_DECREF(v);
        }
        return NULL;
    }
#endif
    return PyErr_SetFromErrno(PySslError);
}

/*
 * format SSl error string
 */
static int PySsl_err_str (unsigned long e, char* buf) {
    unsigned long l = ERR_GET_LIB(e);
    unsigned long f = ERR_GET_FUNC(e);
    unsigned long r = ERR_GET_REASON(e);
    char* ls = (char*)ERR_lib_error_string(e);
    char* fs = (char*)ERR_func_error_string(e);
    char* rs = (char*)ERR_reason_error_string(e);
    char* bp = buf + 2;		/* skip two initial blanks */

    (void)strcpy(buf,"  none:");	/* initialize buffer */
    bp += (ls) ? sprintf(bp,"%s:",ls) :
          ((l) ? sprintf(bp,"lib %lu:",l) : 0);
    bp += (fs) ? sprintf(bp,"%s ",fs) :
          ((f) ? sprintf(bp,"func %lu:",f) : 0);
    bp += (rs) ? sprintf(bp,"%s:",rs) :
          ((r) ? sprintf(bp,"reason(%lu):",r) : 0);
    *bp-- = 0;			/* suppress last divider (:) */
    return (bp - buf);
}

/*
 * report SSL core errors
 */
static PySslObject* PySsl_errors (void) {
    unsigned long e;
    char buf[2 * PY_SSL_ERR_MAX];
    char *bf = buf;

    while (((bf - buf) < PY_SSL_ERR_MAX) && (e = ERR_get_error()))
        bf += PySsl_err_str(e,bf);
    {
        PyObject *v = Py_BuildValue("(sss)", "ssl","core",buf+2);
        if (v != NULL) {
            PyErr_SetObject(PySslError,v);
            Py_DECREF(v);
        }
    }
    return (NULL);
}

/*
 * report SSL application layer errors
 */
static PySslObject* PySsl_app_errors (SSL* s, int ret) {
    int err = SSL_get_error(s,ret);
    char *str;

    switch (err) {
    case SSL_ERROR_SSL:
        return (PySsl_errors());
    case SSL_ERROR_SYSCALL:
        return ((PySslObject *)PySsl_errno());
    case SSL_ERROR_ZERO_RETURN:
        str = "End of data";
        break;
    case SSL_ERROR_WANT_READ:
        str = "Want read";
        break;
    case SSL_ERROR_WANT_WRITE:
        str = "Want write";
        break;
    case SSL_ERROR_WANT_X509_LOOKUP:
        str = "Want x509 lookup";
        break;
    case SSL_ERROR_WANT_CONNECT:
        str = "Want connect";
        break;
    default:
        str = "Unknown";
        break;
    }
    {
        PyObject *v = Py_BuildValue("(sis)", "ssl",err, str);
        if (v != NULL) {
            PyErr_SetObject(PySslError,v);
            Py_DECREF(v);
        }
    }
    return (NULL);
}

/* ssl.read(len) method */

static PyObject* PySslObj_read (PySslObject* self, PyObject* args) {
    int len, n;
    PyObject *buf;

    if (!PyArg_ParseTuple(args,"i",&len))
        return (NULL);
    if (!(buf = PyString_FromStringAndSize((char *)0,len)))
        return (NULL);
    Py_BEGIN_ALLOW_THREADS

    n = SSL_read(self->ssl,PyString_AsString(buf),len);

    Py_END_ALLOW_THREADS

    switch (SSL_get_error(self->ssl,n)) {
    case SSL_ERROR_NONE:		/* good return value */
        break;
    case SSL_ERROR_ZERO_RETURN:
    case SSL_ERROR_SYSCALL:
        if (!n)			/* fix SSL_ERROR_SYCSALL errno=0 case */
            break;
        /* fall thru here */
    default:
        Py_DECREF(buf);
        (void)PySsl_app_errors(self->ssl,n);
        return (NULL);
    }
    if ((n != len) && (_PyString_Resize(&buf,n) < 0))
        return (NULL);
    return (buf);
}

/* ssl.write(data,len) method */

static PyObject* PySslObj_write (PySslObject* self, PyObject * args) {
    char *buf;
    int len, n;
    if (!PyArg_ParseTuple(args, "si", &buf, &len))
        return NULL;

    /* Note: flags are ignored */

    Py_BEGIN_ALLOW_THREADS

    n = SSL_write(self->ssl,buf,len);

    Py_END_ALLOW_THREADS
    if (n < 0)
        return (PySsl_errno());
    return (PyInt_FromLong((long)n));
}

/* ssl.server() method */

static PyObject* PySslObj_server (PySslObject* self, PyObject* args) {
    if (!PyArg_NoArgs(args))
        return (NULL);
    return (PyString_FromString(self->server));
}

/* ssl.issuer() method */

static PyObject* PySslObj_issuer (PySslObject* self, PyObject* args) {
    if (!PyArg_NoArgs(args))
        return (NULL);
    return (PyString_FromString(self->issuer));
}

/* SSL object methods */

static PyMethodDef PySslObj_methods[] = {
    {"read",	(PyCFunction)PySslObj_read,1},
    {"write",	(PyCFunction)PySslObj_write,1},
    {"server",	(PyCFunction)PySslObj_server},
    {"issuer",	(PyCFunction)PySslObj_issuer},
    { NULL, NULL}
};

static void PySsl_dealloc (PySslObject * self) {
    if (self->server_cert)		/* possible not to have one? */
        X509_free(self->server_cert);
    SSL_CTX_free(self->ctx);
    SSL_free(self->ssl);
    Py_XDECREF(self->x_attr);
    PyMem_DEL(self);
}

static PyObject* PySsl_getattr (PySslObject* self, char * name) {
    return (Py_FindMethod(PySslObj_methods,(PyObject *)self,name));
}

staticforward PyTypeObject SSL_Type = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,				/*ob_size*/
    "SSL",				/*tp_name*/
    sizeof(PySslObject),		/*tp_basicsize*/
    0,				/*tp_itemsize*/
    /* methods */
    (destructor)PySsl_dealloc,	/*tp_dealloc*/
    0,				/*tp_print*/
    (getattrfunc)PySsl_getattr,	/*tp_getattr*/
    0,				/*tp_setattr*/
    0,				/*tp_compare*/
    0,				/*tp_repr*/
    0,				/*tp_as_number*/
    0,				/*tp_as_sequence*/
    0,				/*tp_as_mapping*/
    0,				/*tp_hash*/
};

/*
 * C function called for new object initialization
 * Note: SSL protocol version 2, 3, or 2+3 set at compile time
 */
static PySslObject* newPySslObject (int sock_fd) {
    PySslObject *self;
    SSL_METHOD *meth;
    int ret;

#if 0
    meth=SSLv3_client_method();
    meth=SSLv23_client_method();
#endif

    meth=SSLv2_client_method();

    if (!(self = PyObject_NEW(PySslObject,&SSL_Type))) 	/* create new object */
        return (NULL);
    (void)memset(self->server,0,sizeof(self->server));
    (void)memset(self->issuer,0,sizeof(self->issuer));

    self->x_attr = PyDict_New();
    if (!(self->ctx = SSL_CTX_new(meth))) {		/* set up context */
        PyMem_DEL(self);
        return (PySsl_errors());
    }
#if 0				/* Note: set this for v23, Netscape server */
    SSL_CTX_set_options(self->ctx,SSL_OP_ALL);
#endif
    self->ssl = SSL_new(self->ctx);			/* new ssl struct */
    if (!(ret = SSL_set_fd(self->ssl,sock_fd))) {	/* set the socket for SSL */
        PyMem_DEL(self);
        return (PySsl_app_errors(self->ssl,ret));
    }
    SSL_CTX_set_verify(self->ctx,SSL_VERIFY_NONE,NULL); /* set verify lvl */
    SSL_set_connect_state(self->ssl);

    if ((ret = SSL_connect(self->ssl)) < 0) {	/* negotiate SSL connection */
        PyMem_DEL(self);
        return (PySsl_app_errors(self->ssl,ret));
    }
    self->ssl->debug = 1;

    if ((self->server_cert = SSL_get_peer_certificate(self->ssl))) {
        X509_NAME_oneline(X509_get_subject_name(self->server_cert),
                          self->server,sizeof(self->server));
        X509_NAME_oneline(X509_get_issuer_name(self->server_cert),
                          self->issuer, sizeof(self->issuer));
    }
    self->x_attr = NULL;
    self->sock_fd = sock_fd;
    return (self);
}

/*
 * Python function called for new object initialization
 */
static PyObject* PySsl_ssl_new (PyObject* self, PyObject* args) {
    int sock_fd;
    if (!PyArg_ParseTuple(args, "i", &sock_fd))
        return (NULL);
    return ((PyObject *)newPySslObject(sock_fd));
}

/* List of functions exported by this module. */

static PyMethodDef PySsl_methods[] = {
    {"ssl", (PyCFunction)PySsl_ssl_new, METH_VARARGS},
    {NULL, NULL} /* sentinel */

};

/*
 * Initialize this module, called when the first 'import ssl' is done
 */
void
#ifdef WIN32
__declspec(dllexport)
#endif
initssl (void) {
    PyObject *m, *d;
    m = Py_InitModule("ssl", PySsl_methods);
    d = PyModule_GetDict(m);

    SSL_load_error_strings();
    SSLeay_add_ssl_algorithms();

    /* *** Python 1.5 ***
    if (!(PySssl_Error = PyErr_NewException("ssl.error",NULL,NULL)))
     	return;
    */

    if (!(PySslError = PyString_FromString("ssl.error")) ||
            PyDict_SetItemString(d,"error",PySslError))
        Py_FatalError("can't define ssl.error");
    if (PyDict_SetItemString(d,"SSLType",(PyObject *)&SSL_Type))
        return;
}

