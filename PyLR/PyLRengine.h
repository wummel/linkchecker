#ifndef Py_PYLRENGINE_H
#define Py_PYLRENGINE_H
#ifdef __cplusplus
extern "C" {
#endif

#define EOBUF -1

struct inbufdatum {
  PyObject* pylrval;
  int tok;
};

struct inbufdata {
  struct inbufdatum** chunk;
  struct inbufdata* next;
};

typedef struct inbuf_struct {
  struct inbufdata* data;
  int bi;
  int nextinput;
  int chunksize;
} inbuftype;

struct stackdatum {
  int state;
  int tok;
  PyObject* pylrval;
};

struct stackdata {
  struct stackdatum** bucket;
  struct stackdata* next;
};

typedef struct stack_struct {
  struct stackdata* data;
  int si;
  int chunksize;
} stacktype;

typedef struct prodinfo_struct {
  int len;
  PyObject* func;
  int lhsi;
} prodinfo_type;

typedef struct actionstruct{
  int arg;
  short act;
} actiontype;

/***********************************************************************
 * the possible values of the action table
 ***********************************************************************/

#define SHIFT 's'
#define REDUCE 'r'
#define ACCEPT 'a'

typedef struct {
  PyObject_HEAD
  inbuftype* inbuf;
  stacktype* stack;
  prodinfo_type** prodinfo;
  int prodinfosize;
  int** gototable;
  int goto_x;
  int goto_y;
  actiontype*** actiontable;
  int act_x;
  int act_y;
  int toksadded;
} parserobject;


#ifdef __cplusplus
}
#endif
#endif /* !Py_PYLRENGINE_H */
