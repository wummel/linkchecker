/***********************************************************************
 * This file defines an ParseEngine (LR), It references a Parsing table 
 * that is defined in python.
 * 
 * This defines a new type object in Python, called a Parser.  It has 
 * 3  methods, .parse(int: token, char *: text), 
 * of them).  .setaction(production), and .getaction(production).
 *
 * $Id$
 *
 ***********************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include "Python.h"
#include "PyLRengine.h"

/***********************************************************************
 * PyLRengine Error things
 ***********************************************************************/
static PyObject* PyLRParseError;

#define CHECK_MALLOC(obj) \
    if (!(obj = (PyObject *) malloc (sizeof(PyObject)))) { \
	PyErr_SetString(PyExc_MemoryError, "no more memory"); \
        return NULL; \
    }

#define onError(message) \
{ PyErr_SetString(PyExc_ParseError, message); return NULL; }



/***********************************************************************
 * The engines input buffer.  has a chunksize controllable from within 
 * python.  functions are initinbufdata, init_inbuf, incbi, add2buf,
 * gettoken, petpylrval, dumpinbuf
 ***********************************************************************/

static struct inbufdata * init_inbufdata(chunksize)
  int chunksize;
{
  struct inbufdata * ibd;
  int i;
  
  if ((ibd = (struct inbufdata *) malloc(sizeof(struct inbufdata))) == NULL) {
    printf("No more Memory!\n");
    exit(1);
  }
  if ((ibd->chunk = (struct inbufdatum **) malloc(sizeof(struct inbufdatum *) * chunksize)) == NULL) {
    printf("No more Memory!\n");
    exit(1);
  }
  for (i=0; i<chunksize; i++) {
    if ((ibd->chunk[i] = (struct inbufdatum *) malloc(sizeof(struct inbufdatum))) == NULL) {
      onError("Memory");
    }
    ibd->chunk[i]->tok = EOBUF;
    ibd->chunk[i]->pylrval = NULL;
  }
  ibd->next = NULL;
  return ibd;
}

static inbuftype * init_inbuf(chunksize)
  int chunksize;
{
  inbuftype * ib;
  if ((ib = (inbuftype *)malloc(sizeof(inbuftype))) == NULL) {
    printf("No more Memory!\n");
    exit(1);
  }
  ib->bi = 0;
  ib->data = init_inbufdata(chunksize);
  ib->chunksize = chunksize;
  ib->nextinput = 0;
  return ib;
}

static void incbi(inbuf)
  inbuftype * inbuf;
{
  struct inbufdata * tmpdata;
  if ((! ((inbuf->bi + 1) % inbuf->chunksize)) && (inbuf->bi != 0)) {
    tmpdata = inbuf->data->next;
    free(inbuf->data); 
    inbuf->data = tmpdata;
  }
  inbuf->bi++;
}
    
static void add2buf(inbuf, tok, pylrval)
  inbuftype * inbuf; int tok; PyObject * pylrval;
{
  struct inbufdata * orgibd = inbuf->data;
  struct inbufdata * newibd;
  while(inbuf->data->next != NULL) 
    inbuf->data = inbuf->data->next;
  if ((! (inbuf->nextinput % inbuf->chunksize)) && (inbuf->nextinput != 0)) { /* make new chunk at end */
    newibd = init_inbufdata(inbuf->chunksize);
    newibd->chunk[0]->tok = tok;
    newibd->chunk[0]->pylrval = pylrval;
    inbuf->data->next = newibd;
  } else {
    inbuf->data->chunk[(inbuf->nextinput % inbuf->chunksize)]->tok = tok;
    inbuf->data->chunk[(inbuf->nextinput % inbuf->chunksize)]->pylrval = pylrval;
  }
  inbuf->nextinput++;
  inbuf->data = orgibd;
}


#define gettoken(ib) ((ib)->data->chunk[ (ib)->bi % (ib)->chunksize]->tok)
#define getpylrval(ib) ((ib)->data->chunk[ (ib)->bi % (ib)->chunksize]->pylrval)

static void dumpinbuf(inbuf)

  inbuftype* inbuf;
{
  int i, j;
  struct inbufdata * orgibd = inbuf->data;
  printf ("inbuf at %p with bi at %d and chunksize of %d and nextinput at %d:\n", inbuf, \
	  inbuf->bi, inbuf->chunksize, inbuf->nextinput);
  j = 0;
  for (inbuf->data; inbuf->data != NULL; inbuf->data = inbuf->data->next) {
    printf("\tchunk %d:\n", j);
    for (i=0; i < inbuf->chunksize; i++) {
      printf("\t\tchunk[%d]->tok = %d; pylrval at %p\n", 
	     i, 
	     inbuf->data->chunk[i]->tok,
	     inbuf->data->chunk[i]->pylrval);
    }
    j++;
  }
  inbuf->data = orgibd;
}

/***********************************************************************
 * the Stack
 ***********************************************************************/

static stacktype * init_stack (stackchunksize)
  int stackchunksize;
{
  stacktype * newstack;
  if (( newstack = (stacktype *) malloc(sizeof(stacktype))) == NULL) {
    PyErr_SetString(PyLRengineError, "Memory Error");
    return NULL;
  }
  newstack->si = 0;
  newstack->data = NULL;
  newstack->chunksize = stackchunksize;
  return newstack;
}


static struct stackdata * init_stackdata (stackchunksize) 
  int stackchunksize;
{  
  struct stackdata * newstackdata;
  int i;

  if ((newstackdata = (struct stackdata *) malloc (sizeof (struct stackdata))) == NULL) {
   PyErr_SetString(PyLRengineError, "Memory Error");
    return NULL;
  } 
  if ((newstackdata->bucket = (struct stackdatum **) malloc (sizeof (struct stackdatum *) * stackchunksize)) == NULL) {
    PyErr_SetString(PyLRengineError, "Memory Error");
    return NULL;
  } 
  for (i=0; i < stackchunksize; i++) {
    if ((newstackdata->bucket[i] = (struct stackdatum *) malloc(sizeof (struct stackdatum))) == NULL) {
      onError("Memory Error");
    }
    newstackdata->bucket[i]->state = -1;
    newstackdata->bucket[i]->tok = -1;
    newstackdata->bucket[i]->pylrval = NULL;
  }
  newstackdata->next = NULL;
  return newstackdata;
}


static void push (stack, token, state, pylrval) 
  stacktype * stack;
  int token;
  int state;
  PyObject * pylrval;
{
  struct stackdata *newstackdata;
  if (! (stack->si % stack->chunksize)) {
    newstackdata = init_stackdata(stack->chunksize);
    newstackdata->bucket[0]->tok = token;
    newstackdata->bucket[0]->state = state;
    newstackdata->bucket[0]->pylrval = pylrval;
    newstackdata->next = stack->data;
    stack->data = newstackdata;
  } else {
    stack->data->bucket[stack->si % stack->chunksize]->tok = token;
    stack->data->bucket[stack->si % stack->chunksize]->state = state;
    stack->data->bucket[stack->si % stack->chunksize]->pylrval = pylrval;
  }
  Py_XINCREF(pylrval); 
  stack->si++;
}

static void show_stack(stack)
  struct stack_struct * stack;
{
  struct stackdata * orgstackdata;
  int i;
  orgstackdata = stack->data;
  printf("stack at %p:\n", stack);
  for (stack->data; stack->data != NULL; stack->data = stack->data->next) {
    printf("stack->data at %p\n", stack->data);
    for (i=0; i<stack->chunksize; i++) {
      printf ("stack->data->bucket[%d] = (%d, %d, %p)\n", 
	      i, 
	      stack->data->bucket[i]->tok,
	      stack->data->bucket[i]->state,
	      stack->data->bucket[i]->pylrval);
    }
  }
  stack->data = orgstackdata;
}


/***********************************************************************
 * This function returns the python objects stored on the stack so that
 * they can then be passed to the appropriate function (popping the stack
 * only occurs when a reduce operation is called, so the python objects
 * returned get passed to the function associated with the production that
 * is associated with popping items from the stack.  see the method parser_parse
 * for how this works in more detail
 ***********************************************************************/
 
static PyObject **  pop(stack, amt) 
  stacktype * stack;
  int amt;
{
  struct stackdata * tmpsd;
  PyObject ** popped_pylrvals;
  int c = 0;
  if (amt == 0)
    return NULL;
  if ((popped_pylrvals = (PyObject **)malloc(sizeof(PyObject *) * amt)) == NULL)
    onError("Memory Error");
  if (stack->si < amt) {
    PyErr_SetString(PyLRengineError, "popping too much from stack!!!");
    return 0;
  }
  while (amt > 0 && stack->si >= 0) {
    if ((popped_pylrvals[c] = (PyObject *)malloc(sizeof(PyObject))) == NULL)
      onError("Memory Error");
    if ((stack->si - 1) % stack->chunksize) {
      stack->data->bucket[(stack->si -1) % stack->chunksize]->tok = -1;
      stack->data->bucket[(stack->si -1) % stack->chunksize]->state = -1;
      popped_pylrvals[c] = stack->data->bucket[(stack->si -1) % stack->chunksize]->pylrval;
      stack->data->bucket[(stack->si -1) % stack->chunksize]->pylrval = NULL;
    } else {
      stack->data->bucket[0]->tok = -1;
      stack->data->bucket[0]->state = -1;
      popped_pylrvals[c] = stack->data->bucket[0]->pylrval;
      stack->data->bucket[0]->pylrval = NULL;
      tmpsd = stack->data->next;
      free(stack->data); 
      stack->data = tmpsd;
    }
    amt--; stack->si--; c++; /* not quite ;) */
  }
 return popped_pylrvals;
}

#define stackstate(stack) \
(((stack)->data == NULL)?\
 0:\
 (stack)->data->bucket[((stack)->si - 1) % (stack)->chunksize]->state)


/***********************************************************************
 * Production Info related functions
 ***********************************************************************/

static prodinfo_type ** Py_prodinfo2prodinfo (parserobj, py_prodinfo)
  parserobject * parserobj;
  PyObject * py_prodinfo;
{
  prodinfo_type ** prodinfo;
  PyObject * prodtuple;
  int listsize;
  register int listi;
  listsize = PyList_Size(py_prodinfo);
  if (listsize == -1)
    onError("production info table is not a list!");
  parserobj->prodinfosize = listsize;
  if ((prodinfo = (prodinfo_type **) malloc (sizeof (prodinfo_type *) * listsize)) == NULL) 
    onError("No more Mem!");
  for (listi=0; listi < listsize; listi++) {
    if ((prodinfo[listi] = (prodinfo_type *) malloc (sizeof(prodinfo_type))) == NULL)
      onError("Memory");
    prodtuple = PyList_GetItem(py_prodinfo, listi);
    if (! PyTuple_Check(prodtuple)) 
      onError("Corrput Prodinfo table, must contain tuples of (len, callable)");
    prodinfo[listi]->len = (short int) PyInt_AsLong(PyTuple_GetItem(prodtuple, 0));
    if ((prodinfo[listi]->func = (PyObject *) malloc (sizeof(PyObject))) == NULL)
      onError("Memory");
    prodinfo[listi]->func = PyTuple_GetItem(prodtuple, 1);
    prodinfo[listi]->lhsi = (int) PyInt_AsLong(PyTuple_GetItem(prodtuple, 2));
    if ((! PyCallable_Check(prodinfo[listi]->func)) && (prodinfo[listi]->func != Py_None))
      onError("corrupt prodinfo data, must contain tuples of (len, callable)");
    Py_XINCREF(prodinfo[listi]->func);
  }
  return prodinfo;
}

static PyObject * prodinfo2Py_prodinfo(prodinfo, sz)
  prodinfo_type ** prodinfo;
  int sz;
{
  int i;
  PyObject * list;
  PyObject * tuple;
  PyObject * len;
  PyObject * func;
  PyObject * lhsi;
  list = PyList_New(sz);
  for (i=0; i<sz; i++) {
    tuple = PyTuple_New(3);
    len = Py_BuildValue("i", prodinfo[i]->len);
    lhsi = Py_BuildValue("i", prodinfo[i]->lhsi);
    func = prodinfo[i]->func;
    PyTuple_SetItem(tuple, 0, len);
    PyTuple_SetItem(tuple, 1, func);
    PyTuple_SetItem(tuple, 2, lhsi);
    PyList_SetItem(list, i, tuple);
  }
  return list;
}
      
/***********************************************************************
 * the goto table, show and set routines
 ***********************************************************************/

#define GOTOERR -1

static void * mkgototable(parser, pygotos)
  parserobject * parser;
  PyObject * pygotos;
{
  register int outerlen; 
  register int outerct;
  register int innerlen;
  register int innerct;
  int ** gotos;
  PyObject * innerlist;
  PyObject * py_entry;
  outerlen = PyList_Size(pygotos);
  parser->goto_x = 0;
  parser->goto_y = 0;
  parser->gototable = NULL;
  if (outerlen == -1) 
    onError("goto table must be a list of lists!");
  if ((gotos = (int **) malloc(sizeof(int *) * outerlen)) == NULL)
    onError("Memory Error");
  for (outerct = 0; outerct < outerlen; outerct++) {
    innerlist = PyList_GetItem(pygotos, outerct);
    innerlen = PyList_Size(innerlist);
    if (innerlen == -1)
      onError ("goto table must be a list of lists!");
    if ((gotos[outerct] = (int *) malloc (sizeof(int) * innerlen)) == NULL)
      onError("Memory Error");
    for (innerct = 0; innerct < innerlen; innerct++) {
      py_entry = PyList_GetItem(innerlist, innerct);
      if ((! PyInt_Check( py_entry)) && (py_entry != Py_None)) 
	onError("goto table must be a list of list of either ints or None!");
      if (py_entry == Py_None) {
	gotos[outerct][innerct] = GOTOERR;
      }
      else {
	gotos[outerct][innerct] = (int) PyInt_AsLong(py_entry);
      }
    }
  }
  parser->goto_x = outerlen;
  parser->goto_y = innerlen;
  parser->gototable = gotos;
}
      

static PyObject * show_gotos(self, args)
  parserobject * self;
  PyObject * args;
{
  register int x;
  register int y;
  for (x=0; x < self->goto_x; x++) {
    for (y=0; y < self->goto_y; y++) {
      printf("%d ",  self->gototable[x][y]);
    }
    printf ("\n");
  }
  Py_INCREF(Py_None);
  return  Py_None;
}
     
 


/***********************************************************************
 * Action Table set and show
 ***********************************************************************/
#define ACTERR -1

static void * mkactiontable(parser, pyactions)
  parserobject * parser; PyObject * pyactions;
{
  register int outerlen; 
  register int outerct;
  register int innerlen;
  register int innerct;
  actiontype *** actions;
  PyObject * innerlist;
  PyObject * py_tuple;
  PyObject * py_act;
  char * cact;
  PyObject * py_arg;
  int tuplelen;
  parser->act_x = 0;
  parser->act_y = 0;
  parser->actiontable = NULL;
  outerlen = PyList_Size(pyactions);
  if (outerlen == -1) 
    onError("goto table must be a list of lists!");
  if ((actions = (actiontype ***) malloc(sizeof(actiontype *) * outerlen)) == NULL)
    onError("Memory Error");
  for (outerct = 0; outerct < outerlen; outerct++) {
    innerlist = PyList_GetItem(pyactions, outerct);
    innerlen = PyList_Size(innerlist);
    if (innerlen == -1)
      onError ("goto table must be a list of lists!");
    if ((actions[outerct] = (actiontype **) malloc (sizeof(actiontype *) * innerlen)) == NULL)
      onError("Memory Error");
    for (innerct = 0; innerct < innerlen; innerct++) {
      if ((actions[outerct][innerct] = (actiontype *) malloc(sizeof(actiontype))) == NULL)
	onError("Memory Error");
      py_tuple = PyList_GetItem(innerlist, innerct);
      if (! PyTuple_Check(py_tuple)) 
	onError("goto table must be a list of list of tuples!");
      tuplelen = PyTuple_Size(py_tuple);
      if (tuplelen != 2)
	onError("goto table must contain entries of tuples of length 2");
      py_act = PyTuple_GetItem(py_tuple, 0);
      py_arg = PyTuple_GetItem(py_tuple, 1);
      if ((! PyString_Check(py_act)) || (! PyInt_Check(py_arg)))
	onError("goto table's entries must be tuples of type string, int");
      actions[outerct][innerct]->act = (short) *(PyString_AsString(py_act));
      actions[outerct][innerct]->arg = (int) PyInt_AsLong(py_arg);
    }
  }
  parser->act_x = outerlen;
  parser->act_y = innerlen;
  parser->actiontable = actions;
}


static PyObject * show_actions(self, args)
  parserobject * self;
  PyObject * args;
{
  register int x;
  register int y;
  for (x=0; x < self->act_x; x++) {
    for (y=0; y < self->act_y; y++) {
      printf("(%c, %d), ",  self->actiontable[x][y]->act, self->actiontable[x][y]->arg);
    }
    printf ("\n");
  }
  Py_INCREF(Py_None);
  return  Py_None;
}

/***********************************************************************
 * Parser Type Info and internal routines
 ***********************************************************************/


staticforward PyTypeObject ParserType;

#define is_parserobject(v) ((v)->ob_type == &ParserType)


/***********************************************************************
 * Parser Methods
 ***********************************************************************/

static PyObject *
parser_parse(self, args)
  parserobject * self;
  PyObject * args;
{
  int tok, curstate, i, tuple_i;
  PyObject * pylrval;
  PyObject * fargs;
  PyObject * fres;
  actiontype * act;
  PyObject ** pylrvals;
  if (! PyArg_ParseTuple(args, "iO", &tok, &pylrval)) {
    return NULL;
  }
  Py_XINCREF(pylrval);
  add2buf(self->inbuf, tok, pylrval);
  if ( self->toksadded < 1) {
    self->toksadded++;
    return Py_BuildValue("i", 1);
  } 
  if ((stackstate(self->stack) < 0) || (gettoken(self->inbuf) < 0))
    onError("PyLRTableIndexError");
  act = self->actiontable[stackstate(self->stack)][gettoken(self->inbuf)];
  if (act == NULL) {
    onError("PyLRTableError, couldn't retrieve action");
  }
  if (act->act == SHIFT) {
    push(self->stack, gettoken(self->inbuf), act->arg, getpylrval(self->inbuf));
    incbi(self->inbuf);
    return Py_BuildValue("i", 1);
  } else if (act->act == REDUCE) {
    pylrvals = pop(self->stack, self->prodinfo[act->arg - 1]->len);
    if (PyErr_Occurred()) { return NULL; }
    curstate = stackstate(self->stack);
    fargs = PyTuple_New(self->prodinfo[act->arg - 1]->len);
    for (i=0; i < self->prodinfo[act->arg - 1]->len ; i++) {
      tuple_i = ((self->prodinfo[act->arg -1]->len - i) -1);
      PyTuple_SetItem(fargs, tuple_i, pylrvals[i]);
    }
    fres = PyObject_CallObject(self->prodinfo[act->arg - 1]->func, fargs);
    if (PyErr_Occurred())
      return NULL;
    Py_XINCREF(fres);
    /*    Py_DECREF(fargs);*/
    push(self->stack, act->arg, self->gototable[curstate][self->prodinfo[act->arg - 1]->lhsi], fres);
    return Py_BuildValue("i", 1);
  } else if (act->act == ACCEPT) {
    return Py_BuildValue("i", 0);
  } else {
    PyErr_SetString(PyLRengineError, "SyntaxError while parsing");
    return NULL;
  }
}

static PyObject *
parser_show_stack(self, args)
  parserobject * self;
  PyObject * args;
{
  if (! PyArg_ParseTuple(args, ""))
    return NULL;
  show_stack(self->stack);
  Py_XINCREF(Py_None);
  return Py_None;
}

static PyObject *
parser_show_inbuf(self, args)
  parserobject * self;
  PyObject * args;
{
  if (! PyArg_ParseTuple(args, ""))
    return NULL;
  dumpinbuf(self->inbuf);
  Py_XINCREF(Py_None);
  return Py_None;
}


static struct PyMethodDef Parser_methods[] = {
  { "parse",    parser_parse,      1},
  { "showstack", parser_show_stack, 1},
  { "showbuf", parser_show_inbuf, 1},
  { "showgotos", show_gotos, 1},
  { "showacts", show_actions, 1},
  { NULL,       NULL}, /* sentinel */
};

/***********************************************************************
 * Basic type operations for ParserType
 ***********************************************************************/

static parserobject *
newparserobject (pyprodinfo, pyactions, pygotos, bufchunksize, stackchunksize)
  PyObject * pyprodinfo;
  PyObject * pyactions;
  PyObject * pygotos;
  int bufchunksize;
  int stackchunksize;
{
  parserobject *p;
  p = PyObject_NEW(parserobject, &ParserType);
  if (p == NULL) 
    onError("memory in init obj...");
  p->stack = init_stack(stackchunksize);
  p->inbuf = init_inbuf(bufchunksize);
  mkgototable(p, pygotos);
  mkactiontable(p, pyactions);
  p->prodinfo = Py_prodinfo2prodinfo(p, pyprodinfo);
  p->toksadded = 0;
  if (PyErr_Occurred()) 
    return NULL;
  return p;
}

static void
parser_dealloc(self)
  parserobject *self;
{
  PyMem_DEL(self); 
}

static int
parser_print(self, fp, flags)
  parserobject * self;
  FILE * fp;
  int flags;
{
  fprintf(fp, "<PyLRengine Object at %p>\n", self);
  return 0;
}


static PyObject *
parser_getattr(self, name)
  parserobject * self;
  char * name;
{
  if (strcmp(name, "state") == 0) 
    return Py_BuildValue("i", stackstate(self->stack));
  if (strcmp(name, "stacksize") == 0)
    return Py_BuildValue("i", (self->stack->si));
  if (strcmp(name, "prodinfo") == 0) 
    return prodinfo2Py_prodinfo(self->prodinfo, self->prodinfosize);
  if (strcmp(name, "__members__") == 0)
    return Py_BuildValue("[sss]", "state", "stacksize", "prodinfo");
  else
    return Py_FindMethod(Parser_methods, (PyObject *) self, name);
}

    
static PyTypeObject ParserType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,
  "NewEngine",                         /* type name */
  sizeof(parserobject),             /* basic size */
  0,                                /* itemsize */ 
  (destructor) parser_dealloc,       
  (printfunc)  parser_print,
  (getattrfunc) parser_getattr
};


/***********************************************************************
 * Module Logic
 ***********************************************************************/

static PyObject *
parsernew(self, args)
PyObject* self;
PyObject* args;
{
    PyObject* pyprodlengths = NULL;
    PyObject* pyactions = NULL;
    PyObject* pygotos = NULL;
    PyObject* res = NULL;
    int bufchunksize=50;
    int stackchunksize=100;
    CHECK_MALLOC(pyprodlengths)
    CHECK_MALLOC(pyactions)
    CHECK_MALLOC(pygotos)
    if (!PyArg_ParseTuple(args, "O!O!O!|ii", &PyList_Type, &pyprodlengths,
			  &PyList_Type, &pyactions, &PyList_Type, &pygotos,
			  &bufchunksize, &stackchunksize))
	goto finally;
    res = (PyObject*) newparserobject(pyprodlengths, pyactions, pygotos, bufchunksize, stackchunksize);
finally:
    Py_XDECREF(pyprodlengths);
    Py_XDECREF(pyactions);
    Py_XDECREF(pygotos);
    return res;
}


static struct PyMethodDef PyLRengine_methods[] = {
    {"NewEngine",  (PyCFunction)parsernew},
    {NULL, NULL}
};


void
initPyLRengine()
{
    PyObject *m, *d;
    m = Py_InitModule("PyLRengine", PyLRengine_methods);
    d = PyModule_GetDict(m);
    if (PyErr_Occurred())
	Py_FatalError("can't initialize module PyLRengine");
}













