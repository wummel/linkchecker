/* A Bison parser, made by GNU Bison 1.875d.  */

/* Skeleton parser for Yacc-like parsing with Bison,
   Copyright (C) 1984, 1989, 1990, 2000, 2001, 2002, 2003, 2004 Free Software Foundation, Inc.

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2, or (at your option)
   any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  */

/* As a special exception, when this file is copied by Bison into a
   Bison output file, you may use that output file without restriction.
   This special exception was added by the Free Software Foundation
   in version 1.24 of Bison.  */

/* Written by Richard Stallman by simplifying the original so called
   ``semantic'' parser.  */

/* All symbols defined below should begin with yy or YY, to avoid
   infringing on user name space.  This should be done even for local
   variables, as they might otherwise be expanded by user macros.
   There are some unavoidable exceptions within include files to
   define necessary library symbols; they are noted "INFRINGES ON
   USER NAME SPACE" below.  */

/* Identify Bison output.  */
#define YYBISON 1

/* Skeleton name.  */
#define YYSKELETON_NAME "yacc.c"

/* Pure parsers.  */
#define YYPURE 1

/* Using locations.  */
#define YYLSP_NEEDED 0



/* Tokens.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
   /* Put the tokens into the symbol table, so that GDB and other debuggers
      know about them.  */
   enum yytokentype {
     T_WAIT = 258,
     T_ERROR = 259,
     T_TEXT = 260,
     T_ELEMENT_START = 261,
     T_ELEMENT_START_END = 262,
     T_ELEMENT_END = 263,
     T_SCRIPT = 264,
     T_STYLE = 265,
     T_PI = 266,
     T_COMMENT = 267,
     T_CDATA = 268,
     T_DOCTYPE = 269
   };
#endif
#define T_WAIT 258
#define T_ERROR 259
#define T_TEXT 260
#define T_ELEMENT_START 261
#define T_ELEMENT_START_END 262
#define T_ELEMENT_END 263
#define T_SCRIPT 264
#define T_STYLE 265
#define T_PI 266
#define T_COMMENT 267
#define T_CDATA 268
#define T_DOCTYPE 269




/* Copy the first part of user declarations.  */
#line 1 "htmlparse.y"

/* Copyright (C) 2000-2004  Bastian Kleineidam

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
*/
/* Python module definition of a SAX html parser */
#include "htmlsax.h"
#include "structmember.h"
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

/* parser.resolve_entities */
static PyObject* resolve_entities;
/* ListDict class, sorted dictionary */
static PyObject* list_dict;
/* set_encoding helper function */
static PyObject* set_encoding;
/* set_doctype helper function */
static PyObject* set_doctype;

/* macros for easier scanner state manipulation */

/* clear buffer b, returning NULL on error */
#define CLEAR_BUF(b) \
    b = PyMem_Resize(b, char, 1); \
    if (b==NULL) return NULL; \
    (b)[0] = '\0'

/* clear buffer b, returning NULL and decref self on error */
#define CLEAR_BUF_DECREF(self, b) \
    b = PyMem_Resize(b, char, 1); \
    if (b==NULL) { Py_DECREF(self); return NULL; } \
    (b)[0] = '\0'

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
    /* the handler object */
    PyObject* handler;
    /* the charset encoding (PyStringObject) */
    PyObject* encoding;
    /* the document type (PyStringObject) */
    PyObject* doctype;
    UserData* userData;
    void* scanner;
} parser_object;

staticforward PyTypeObject parser_type;

/* use Pythons memory management */
#define YYMALLOC PyMem_Malloc
#define YYFREE PyMem_Free

/* Test whether tag does not need an HTML end tag. Return -1 on error. */
static int html_end_tag (PyObject* ptag, PyObject* parser) {
    PyObject* pdoctype;
    char* doctype;
    int ret = 1;
    pdoctype = PyObject_GetAttrString(parser, "doctype");
    if (pdoctype==NULL) return -1;
    doctype = PyString_AsString(pdoctype);
    if (doctype == NULL) { Py_DECREF(pdoctype); return -1; }
    if (strcmp(doctype, "HTML")==0) {
        char* tag = PyString_AsString(ptag);
        if (tag == NULL) { Py_DECREF(pdoctype); return -1; }
        ret = strcmp(tag, "area")!=0 &&
            strcmp(tag, "base")!=0 &&
            strcmp(tag, "basefont")!=0 &&
            strcmp(tag, "br")!=0 &&
            strcmp(tag, "col")!=0 &&
            strcmp(tag, "frame")!=0 &&
            strcmp(tag, "hr")!=0 &&
            strcmp(tag, "img")!=0 &&
            strcmp(tag, "input")!=0 &&
            strcmp(tag, "isindex")!=0 &&
            strcmp(tag, "link")!=0 &&
            strcmp(tag, "meta")!=0 &&
            strcmp(tag, "param")!=0;
    }
    /* it is not HTML (presumably XHTML) */
    Py_DECREF(pdoctype);
    return ret;
}



/* Enabling traces.  */
#ifndef YYDEBUG
# define YYDEBUG 1
#endif

/* Enabling verbose error messages.  */
#ifdef YYERROR_VERBOSE
# undef YYERROR_VERBOSE
# define YYERROR_VERBOSE 1
#else
# define YYERROR_VERBOSE 0
#endif

#if ! defined (YYSTYPE) && ! defined (YYSTYPE_IS_DECLARED)
typedef int YYSTYPE;
# define yystype YYSTYPE /* obsolescent; will be withdrawn */
# define YYSTYPE_IS_DECLARED 1
# define YYSTYPE_IS_TRIVIAL 1
#endif



/* Copy the second part of user declarations.  */


/* Line 214 of yacc.c.  */
#line 259 "htmlparse.c"

#if ! defined (yyoverflow) || YYERROR_VERBOSE

# ifndef YYFREE
#  define YYFREE free
# endif
# ifndef YYMALLOC
#  define YYMALLOC malloc
# endif

/* The parser invokes alloca or malloc; define the necessary symbols.  */

# ifdef YYSTACK_USE_ALLOCA
#  if YYSTACK_USE_ALLOCA
#   define YYSTACK_ALLOC alloca
#  endif
# else
#  if defined (alloca) || defined (_ALLOCA_H)
#   define YYSTACK_ALLOC alloca
#  else
#   ifdef __GNUC__
#    define YYSTACK_ALLOC __builtin_alloca
#   endif
#  endif
# endif

# ifdef YYSTACK_ALLOC
   /* Pacify GCC's `empty if-body' warning. */
#  define YYSTACK_FREE(Ptr) do { /* empty */; } while (0)
# else
#  if defined (__STDC__) || defined (__cplusplus)
#   include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#   define YYSIZE_T size_t
#  endif
#  define YYSTACK_ALLOC YYMALLOC
#  define YYSTACK_FREE YYFREE
# endif
#endif /* ! defined (yyoverflow) || YYERROR_VERBOSE */


#if (! defined (yyoverflow) \
     && (! defined (__cplusplus) \
	 || (defined (YYSTYPE_IS_TRIVIAL) && YYSTYPE_IS_TRIVIAL)))

/* A type that is properly aligned for any stack member.  */
union yyalloc
{
  short int yyss;
  YYSTYPE yyvs;
  };

/* The size of the maximum gap between one aligned stack and the next.  */
# define YYSTACK_GAP_MAXIMUM (sizeof (union yyalloc) - 1)

/* The size of an array large to enough to hold all stacks, each with
   N elements.  */
# define YYSTACK_BYTES(N) \
     ((N) * (sizeof (short int) + sizeof (YYSTYPE))			\
      + YYSTACK_GAP_MAXIMUM)

/* Copy COUNT objects from FROM to TO.  The source and destination do
   not overlap.  */
# ifndef YYCOPY
#  if defined (__GNUC__) && 1 < __GNUC__
#   define YYCOPY(To, From, Count) \
      __builtin_memcpy (To, From, (Count) * sizeof (*(From)))
#  else
#   define YYCOPY(To, From, Count)		\
      do					\
	{					\
	  register YYSIZE_T yyi;		\
	  for (yyi = 0; yyi < (Count); yyi++)	\
	    (To)[yyi] = (From)[yyi];		\
	}					\
      while (0)
#  endif
# endif

/* Relocate STACK from its old location to the new one.  The
   local variables YYSIZE and YYSTACKSIZE give the old and new number of
   elements in the stack, and YYPTR gives the new location of the
   stack.  Advance YYPTR to a properly aligned location for the next
   stack.  */
# define YYSTACK_RELOCATE(Stack)					\
    do									\
      {									\
	YYSIZE_T yynewbytes;						\
	YYCOPY (&yyptr->Stack, Stack, yysize);				\
	Stack = &yyptr->Stack;						\
	yynewbytes = yystacksize * sizeof (*Stack) + YYSTACK_GAP_MAXIMUM; \
	yyptr += yynewbytes / sizeof (*yyptr);				\
      }									\
    while (0)

#endif

#if defined (__STDC__) || defined (__cplusplus)
   typedef signed char yysigned_char;
#else
   typedef short int yysigned_char;
#endif

/* YYFINAL -- State number of the termination state. */
#define YYFINAL  15
/* YYLAST -- Last index in YYTABLE.  */
#define YYLAST   26

/* YYNTOKENS -- Number of terminals. */
#define YYNTOKENS  15
/* YYNNTS -- Number of nonterminals. */
#define YYNNTS  3
/* YYNRULES -- Number of rules. */
#define YYNRULES  15
/* YYNRULES -- Number of states. */
#define YYNSTATES  17

/* YYTRANSLATE(YYLEX) -- Bison symbol number corresponding to YYLEX.  */
#define YYUNDEFTOK  2
#define YYMAXUTOK   269

#define YYTRANSLATE(YYX) 						\
  ((unsigned int) (YYX) <= YYMAXUTOK ? yytranslate[YYX] : YYUNDEFTOK)

/* YYTRANSLATE[YYLEX] -- Bison symbol number corresponding to YYLEX.  */
static const unsigned char yytranslate[] =
{
       0,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     1,     2,     3,     4,
       5,     6,     7,     8,     9,    10,    11,    12,    13,    14
};

#if YYDEBUG
/* YYPRHS[YYN] -- Index of the first RHS symbol of rule number YYN in
   YYRHS.  */
static const unsigned char yyprhs[] =
{
       0,     0,     3,     5,     8,    10,    12,    14,    16,    18,
      20,    22,    24,    26,    28,    30
};

/* YYRHS -- A `-1'-separated list of the rules' RHS. */
static const yysigned_char yyrhs[] =
{
      16,     0,    -1,    17,    -1,    16,    17,    -1,     3,    -1,
       4,    -1,     6,    -1,     7,    -1,     8,    -1,    12,    -1,
      11,    -1,    13,    -1,    14,    -1,     9,    -1,    10,    -1,
       5,    -1
};

/* YYRLINE[YYN] -- source line where rule number YYN was defined.  */
static const unsigned short int yyrline[] =
{
       0,   169,   169,   170,   173,   174,   181,   220,   267,   301,
     322,   343,   364,   389,   414,   439
};
#endif

#if YYDEBUG || YYERROR_VERBOSE
/* YYTNME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
   First, the terminals, then, starting at YYNTOKENS, nonterminals. */
static const char *const yytname[] =
{
  "$end", "error", "$undefined", "T_WAIT", "T_ERROR", "T_TEXT",
  "T_ELEMENT_START", "T_ELEMENT_START_END", "T_ELEMENT_END", "T_SCRIPT",
  "T_STYLE", "T_PI", "T_COMMENT", "T_CDATA", "T_DOCTYPE", "$accept",
  "elements", "element", 0
};
#endif

# ifdef YYPRINT
/* YYTOKNUM[YYLEX-NUM] -- Internal token number corresponding to
   token YYLEX-NUM.  */
static const unsigned short int yytoknum[] =
{
       0,   256,   257,   258,   259,   260,   261,   262,   263,   264,
     265,   266,   267,   268,   269
};
# endif

/* YYR1[YYN] -- Symbol number of symbol that rule YYN derives.  */
static const unsigned char yyr1[] =
{
       0,    15,    16,    16,    17,    17,    17,    17,    17,    17,
      17,    17,    17,    17,    17,    17
};

/* YYR2[YYN] -- Number of symbols composing right hand side of rule YYN.  */
static const unsigned char yyr2[] =
{
       0,     2,     1,     2,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     1,     1,     1
};

/* YYDEFACT[STATE-NAME] -- Default rule to reduce with in state
   STATE-NUM when YYTABLE doesn't specify something else to do.  Zero
   means the default is an error.  */
static const unsigned char yydefact[] =
{
       0,     4,     5,    15,     6,     7,     8,    13,    14,    10,
       9,    11,    12,     0,     2,     1,     3
};

/* YYDEFGOTO[NTERM-NUM]. */
static const yysigned_char yydefgoto[] =
{
      -1,    13,    14
};

/* YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
   STATE-NUM.  */
#define YYPACT_NINF -13
static const yysigned_char yypact[] =
{
      12,   -13,   -13,   -13,   -13,   -13,   -13,   -13,   -13,   -13,
     -13,   -13,   -13,     0,   -13,   -13,   -13
};

/* YYPGOTO[NTERM-NUM].  */
static const yysigned_char yypgoto[] =
{
     -13,   -13,   -12
};

/* YYTABLE[YYPACT[STATE-NUM]].  What to do in state STATE-NUM.  If
   positive, shift that token.  If negative, reduce the rule which
   number is the opposite.  If zero, do what YYDEFACT says.
   If YYTABLE_NINF, syntax error.  */
#define YYTABLE_NINF -1
static const unsigned char yytable[] =
{
      15,    16,     0,     1,     2,     3,     4,     5,     6,     7,
       8,     9,    10,    11,    12,     1,     2,     3,     4,     5,
       6,     7,     8,     9,    10,    11,    12
};

static const yysigned_char yycheck[] =
{
       0,    13,    -1,     3,     4,     5,     6,     7,     8,     9,
      10,    11,    12,    13,    14,     3,     4,     5,     6,     7,
       8,     9,    10,    11,    12,    13,    14
};

/* YYSTOS[STATE-NUM] -- The (internal number of the) accessing
   symbol of state STATE-NUM.  */
static const unsigned char yystos[] =
{
       0,     3,     4,     5,     6,     7,     8,     9,    10,    11,
      12,    13,    14,    16,    17,     0,    17
};

#if ! defined (YYSIZE_T) && defined (__SIZE_TYPE__)
# define YYSIZE_T __SIZE_TYPE__
#endif
#if ! defined (YYSIZE_T) && defined (size_t)
# define YYSIZE_T size_t
#endif
#if ! defined (YYSIZE_T)
# if defined (__STDC__) || defined (__cplusplus)
#  include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  define YYSIZE_T size_t
# endif
#endif
#if ! defined (YYSIZE_T)
# define YYSIZE_T unsigned int
#endif

#define yyerrok		(yyerrstatus = 0)
#define yyclearin	(yychar = YYEMPTY)
#define YYEMPTY		(-2)
#define YYEOF		0

#define YYACCEPT	goto yyacceptlab
#define YYABORT		goto yyabortlab
#define YYERROR		goto yyerrorlab


/* Like YYERROR except do call yyerror.  This remains here temporarily
   to ease the transition to the new meaning of YYERROR, for GCC.
   Once GCC version 2 has supplanted version 1, this can go.  */

#define YYFAIL		goto yyerrlab

#define YYRECOVERING()  (!!yyerrstatus)

#define YYBACKUP(Token, Value)					\
do								\
  if (yychar == YYEMPTY && yylen == 1)				\
    {								\
      yychar = (Token);						\
      yylval = (Value);						\
      yytoken = YYTRANSLATE (yychar);				\
      YYPOPSTACK;						\
      goto yybackup;						\
    }								\
  else								\
    { 								\
      yyerror ("syntax error: cannot back up");\
      YYERROR;							\
    }								\
while (0)

#define YYTERROR	1
#define YYERRCODE	256

/* YYLLOC_DEFAULT -- Compute the default location (before the actions
   are run).  */

#ifndef YYLLOC_DEFAULT
# define YYLLOC_DEFAULT(Current, Rhs, N)		\
   ((Current).first_line   = (Rhs)[1].first_line,	\
    (Current).first_column = (Rhs)[1].first_column,	\
    (Current).last_line    = (Rhs)[N].last_line,	\
    (Current).last_column  = (Rhs)[N].last_column)
#endif

/* YYLEX -- calling `yylex' with the right arguments.  */

#ifdef YYLEX_PARAM
# define YYLEX yylex (&yylval, YYLEX_PARAM)
#else
# define YYLEX yylex (&yylval)
#endif

/* Enable debugging if requested.  */
#if YYDEBUG

# ifndef YYFPRINTF
#  include <stdio.h> /* INFRINGES ON USER NAME SPACE */
#  define YYFPRINTF fprintf
# endif

# define YYDPRINTF(Args)			\
do {						\
  if (yydebug)					\
    YYFPRINTF Args;				\
} while (0)

# define YYDSYMPRINT(Args)			\
do {						\
  if (yydebug)					\
    yysymprint Args;				\
} while (0)

# define YYDSYMPRINTF(Title, Token, Value, Location)		\
do {								\
  if (yydebug)							\
    {								\
      YYFPRINTF (stderr, "%s ", Title);				\
      yysymprint (stderr, 					\
                  Token, Value);	\
      YYFPRINTF (stderr, "\n");					\
    }								\
} while (0)

/*------------------------------------------------------------------.
| yy_stack_print -- Print the state stack from its BOTTOM up to its |
| TOP (included).                                                   |
`------------------------------------------------------------------*/

#if defined (__STDC__) || defined (__cplusplus)
static void
yy_stack_print (short int *bottom, short int *top)
#else
static void
yy_stack_print (bottom, top)
    short int *bottom;
    short int *top;
#endif
{
  YYFPRINTF (stderr, "Stack now");
  for (/* Nothing. */; bottom <= top; ++bottom)
    YYFPRINTF (stderr, " %d", *bottom);
  YYFPRINTF (stderr, "\n");
}

# define YY_STACK_PRINT(Bottom, Top)				\
do {								\
  if (yydebug)							\
    yy_stack_print ((Bottom), (Top));				\
} while (0)


/*------------------------------------------------.
| Report that the YYRULE is going to be reduced.  |
`------------------------------------------------*/

#if defined (__STDC__) || defined (__cplusplus)
static void
yy_reduce_print (int yyrule)
#else
static void
yy_reduce_print (yyrule)
    int yyrule;
#endif
{
  int yyi;
  unsigned int yylno = yyrline[yyrule];
  YYFPRINTF (stderr, "Reducing stack by rule %d (line %u), ",
             yyrule - 1, yylno);
  /* Print the symbols being reduced, and their result.  */
  for (yyi = yyprhs[yyrule]; 0 <= yyrhs[yyi]; yyi++)
    YYFPRINTF (stderr, "%s ", yytname [yyrhs[yyi]]);
  YYFPRINTF (stderr, "-> %s\n", yytname [yyr1[yyrule]]);
}

# define YY_REDUCE_PRINT(Rule)		\
do {					\
  if (yydebug)				\
    yy_reduce_print (Rule);		\
} while (0)

/* Nonzero means print parse trace.  It is left uninitialized so that
   multiple parsers can coexist.  */
int yydebug;
#else /* !YYDEBUG */
# define YYDPRINTF(Args)
# define YYDSYMPRINT(Args)
# define YYDSYMPRINTF(Title, Token, Value, Location)
# define YY_STACK_PRINT(Bottom, Top)
# define YY_REDUCE_PRINT(Rule)
#endif /* !YYDEBUG */


/* YYINITDEPTH -- initial size of the parser's stacks.  */
#ifndef	YYINITDEPTH
# define YYINITDEPTH 200
#endif

/* YYMAXDEPTH -- maximum size the stacks can grow to (effective only
   if the built-in stack extension method is used).

   Do not make this value too large; the results are undefined if
   SIZE_MAX < YYSTACK_BYTES (YYMAXDEPTH)
   evaluated with infinite-precision integer arithmetic.  */

#if defined (YYMAXDEPTH) && YYMAXDEPTH == 0
# undef YYMAXDEPTH
#endif

#ifndef YYMAXDEPTH
# define YYMAXDEPTH 10000
#endif



#if YYERROR_VERBOSE

# ifndef yystrlen
#  if defined (__GLIBC__) && defined (_STRING_H)
#   define yystrlen strlen
#  else
/* Return the length of YYSTR.  */
static YYSIZE_T
#   if defined (__STDC__) || defined (__cplusplus)
yystrlen (const char *yystr)
#   else
yystrlen (yystr)
     const char *yystr;
#   endif
{
  register const char *yys = yystr;

  while (*yys++ != '\0')
    continue;

  return yys - yystr - 1;
}
#  endif
# endif

# ifndef yystpcpy
#  if defined (__GLIBC__) && defined (_STRING_H) && defined (_GNU_SOURCE)
#   define yystpcpy stpcpy
#  else
/* Copy YYSRC to YYDEST, returning the address of the terminating '\0' in
   YYDEST.  */
static char *
#   if defined (__STDC__) || defined (__cplusplus)
yystpcpy (char *yydest, const char *yysrc)
#   else
yystpcpy (yydest, yysrc)
     char *yydest;
     const char *yysrc;
#   endif
{
  register char *yyd = yydest;
  register const char *yys = yysrc;

  while ((*yyd++ = *yys++) != '\0')
    continue;

  return yyd - 1;
}
#  endif
# endif

#endif /* !YYERROR_VERBOSE */



#if YYDEBUG
/*--------------------------------.
| Print this symbol on YYOUTPUT.  |
`--------------------------------*/

#if defined (__STDC__) || defined (__cplusplus)
static void
yysymprint (FILE *yyoutput, int yytype, YYSTYPE *yyvaluep)
#else
static void
yysymprint (yyoutput, yytype, yyvaluep)
    FILE *yyoutput;
    int yytype;
    YYSTYPE *yyvaluep;
#endif
{
  /* Pacify ``unused variable'' warnings.  */
  (void) yyvaluep;

  if (yytype < YYNTOKENS)
    {
      YYFPRINTF (yyoutput, "token %s (", yytname[yytype]);
# ifdef YYPRINT
      YYPRINT (yyoutput, yytoknum[yytype], *yyvaluep);
# endif
    }
  else
    YYFPRINTF (yyoutput, "nterm %s (", yytname[yytype]);

  switch (yytype)
    {
      default:
        break;
    }
  YYFPRINTF (yyoutput, ")");
}

#endif /* ! YYDEBUG */
/*-----------------------------------------------.
| Release the memory associated to this symbol.  |
`-----------------------------------------------*/

#if defined (__STDC__) || defined (__cplusplus)
static void
yydestruct (int yytype, YYSTYPE *yyvaluep)
#else
static void
yydestruct (yytype, yyvaluep)
    int yytype;
    YYSTYPE *yyvaluep;
#endif
{
  /* Pacify ``unused variable'' warnings.  */
  (void) yyvaluep;

  switch (yytype)
    {

      default:
        break;
    }
}


/* Prevent warnings from -Wmissing-prototypes.  */

#ifdef YYPARSE_PARAM
# if defined (__STDC__) || defined (__cplusplus)
int yyparse (void *YYPARSE_PARAM);
# else
int yyparse ();
# endif
#else /* ! YYPARSE_PARAM */
#if defined (__STDC__) || defined (__cplusplus)
int yyparse (void);
#else
int yyparse ();
#endif
#endif /* ! YYPARSE_PARAM */






/*----------.
| yyparse.  |
`----------*/

#ifdef YYPARSE_PARAM
# if defined (__STDC__) || defined (__cplusplus)
int yyparse (void *YYPARSE_PARAM)
# else
int yyparse (YYPARSE_PARAM)
  void *YYPARSE_PARAM;
# endif
#else /* ! YYPARSE_PARAM */
#if defined (__STDC__) || defined (__cplusplus)
int
yyparse (void)
#else
int
yyparse ()

#endif
#endif
{
  /* The lookahead symbol.  */
int yychar;

/* The semantic value of the lookahead symbol.  */
YYSTYPE yylval;

/* Number of syntax errors so far.  */
int yynerrs;

  register int yystate;
  register int yyn;
  int yyresult;
  /* Number of tokens to shift before error messages enabled.  */
  int yyerrstatus;
  /* Lookahead token as an internal (translated) token number.  */
  int yytoken = 0;

  /* Three stacks and their tools:
     `yyss': related to states,
     `yyvs': related to semantic values,
     `yyls': related to locations.

     Refer to the stacks thru separate pointers, to allow yyoverflow
     to reallocate them elsewhere.  */

  /* The state stack.  */
  short int yyssa[YYINITDEPTH];
  short int *yyss = yyssa;
  register short int *yyssp;

  /* The semantic value stack.  */
  YYSTYPE yyvsa[YYINITDEPTH];
  YYSTYPE *yyvs = yyvsa;
  register YYSTYPE *yyvsp;



#define YYPOPSTACK   (yyvsp--, yyssp--)

  YYSIZE_T yystacksize = YYINITDEPTH;

  /* The variables used to return semantic value and location from the
     action routines.  */
  YYSTYPE yyval;


  /* When reducing, the number of symbols on the RHS of the reduced
     rule.  */
  int yylen;

  YYDPRINTF ((stderr, "Starting parse\n"));

  yystate = 0;
  yyerrstatus = 0;
  yynerrs = 0;
  yychar = YYEMPTY;		/* Cause a token to be read.  */

  /* Initialize stack pointers.
     Waste one element of value and location stack
     so that they stay on the same level as the state stack.
     The wasted elements are never initialized.  */

  yyssp = yyss;
  yyvsp = yyvs;


  goto yysetstate;

/*------------------------------------------------------------.
| yynewstate -- Push a new state, which is found in yystate.  |
`------------------------------------------------------------*/
 yynewstate:
  /* In all cases, when you get here, the value and location stacks
     have just been pushed. so pushing a state here evens the stacks.
     */
  yyssp++;

 yysetstate:
  *yyssp = yystate;

  if (yyss + yystacksize - 1 <= yyssp)
    {
      /* Get the current used size of the three stacks, in elements.  */
      YYSIZE_T yysize = yyssp - yyss + 1;

#ifdef yyoverflow
      {
	/* Give user a chance to reallocate the stack. Use copies of
	   these so that the &'s don't force the real ones into
	   memory.  */
	YYSTYPE *yyvs1 = yyvs;
	short int *yyss1 = yyss;


	/* Each stack pointer address is followed by the size of the
	   data in use in that stack, in bytes.  This used to be a
	   conditional around just the two extra args, but that might
	   be undefined if yyoverflow is a macro.  */
	yyoverflow ("parser stack overflow",
		    &yyss1, yysize * sizeof (*yyssp),
		    &yyvs1, yysize * sizeof (*yyvsp),

		    &yystacksize);

	yyss = yyss1;
	yyvs = yyvs1;
      }
#else /* no yyoverflow */
# ifndef YYSTACK_RELOCATE
      goto yyoverflowlab;
# else
      /* Extend the stack our own way.  */
      if (YYMAXDEPTH <= yystacksize)
	goto yyoverflowlab;
      yystacksize *= 2;
      if (YYMAXDEPTH < yystacksize)
	yystacksize = YYMAXDEPTH;

      {
	short int *yyss1 = yyss;
	union yyalloc *yyptr =
	  (union yyalloc *) YYSTACK_ALLOC (YYSTACK_BYTES (yystacksize));
	if (! yyptr)
	  goto yyoverflowlab;
	YYSTACK_RELOCATE (yyss);
	YYSTACK_RELOCATE (yyvs);

#  undef YYSTACK_RELOCATE
	if (yyss1 != yyssa)
	  YYSTACK_FREE (yyss1);
      }
# endif
#endif /* no yyoverflow */

      yyssp = yyss + yysize - 1;
      yyvsp = yyvs + yysize - 1;


      YYDPRINTF ((stderr, "Stack size increased to %lu\n",
		  (unsigned long int) yystacksize));

      if (yyss + yystacksize - 1 <= yyssp)
	YYABORT;
    }

  YYDPRINTF ((stderr, "Entering state %d\n", yystate));

  goto yybackup;

/*-----------.
| yybackup.  |
`-----------*/
yybackup:

/* Do appropriate processing given the current state.  */
/* Read a lookahead token if we need one and don't already have one.  */
/* yyresume: */

  /* First try to decide what to do without reference to lookahead token.  */

  yyn = yypact[yystate];
  if (yyn == YYPACT_NINF)
    goto yydefault;

  /* Not known => get a lookahead token if don't already have one.  */

  /* YYCHAR is either YYEMPTY or YYEOF or a valid lookahead symbol.  */
  if (yychar == YYEMPTY)
    {
      YYDPRINTF ((stderr, "Reading a token: "));
      yychar = YYLEX;
    }

  if (yychar <= YYEOF)
    {
      yychar = yytoken = YYEOF;
      YYDPRINTF ((stderr, "Now at end of input.\n"));
    }
  else
    {
      yytoken = YYTRANSLATE (yychar);
      YYDSYMPRINTF ("Next token is", yytoken, &yylval, &yylloc);
    }

  /* If the proper action on seeing token YYTOKEN is to reduce or to
     detect an error, take that action.  */
  yyn += yytoken;
  if (yyn < 0 || YYLAST < yyn || yycheck[yyn] != yytoken)
    goto yydefault;
  yyn = yytable[yyn];
  if (yyn <= 0)
    {
      if (yyn == 0 || yyn == YYTABLE_NINF)
	goto yyerrlab;
      yyn = -yyn;
      goto yyreduce;
    }

  if (yyn == YYFINAL)
    YYACCEPT;

  /* Shift the lookahead token.  */
  YYDPRINTF ((stderr, "Shifting token %s, ", yytname[yytoken]));

  /* Discard the token being shifted unless it is eof.  */
  if (yychar != YYEOF)
    yychar = YYEMPTY;

  *++yyvsp = yylval;


  /* Count tokens shifted since error; after three, turn off error
     status.  */
  if (yyerrstatus)
    yyerrstatus--;

  yystate = yyn;
  goto yynewstate;


/*-----------------------------------------------------------.
| yydefault -- do the default action for the current state.  |
`-----------------------------------------------------------*/
yydefault:
  yyn = yydefact[yystate];
  if (yyn == 0)
    goto yyerrlab;
  goto yyreduce;


/*-----------------------------.
| yyreduce -- Do a reduction.  |
`-----------------------------*/
yyreduce:
  /* yyn is the number of a rule to reduce with.  */
  yylen = yyr2[yyn];

  /* If YYLEN is nonzero, implement the default value of the action:
     `$$ = $1'.

     Otherwise, the following line sets YYVAL to garbage.
     This behavior is undocumented and Bison
     users should not rely upon it.  Assigning to YYVAL
     unconditionally makes the parser a bit smaller, and it avoids a
     GCC warning that YYVAL may be used uninitialized.  */
  yyval = yyvsp[1-yylen];


  YY_REDUCE_PRINT (yyn);
  switch (yyn)
    {
        case 2:
#line 169 "htmlparse.y"
    {;}
    break;

  case 3:
#line 170 "htmlparse.y"
    {;}
    break;

  case 4:
#line 173 "htmlparse.y"
    { YYACCEPT; /* wait for more lexer input */ ;}
    break;

  case 5:
#line 175 "htmlparse.y"
    {
    /* an error occured in the scanner, the python exception must be set */
    UserData* ud = yyget_extra(scanner);
    PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
    YYABORT;
;}
    break;

  case 6:
#line 182 "htmlparse.y"
    {
    /* $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a PyDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM(yyvsp[0], 0);
    PyObject* attrs = PyTuple_GET_ITEM(yyvsp[0], 1);
    int error = 0;
    if (tag==NULL || attrs==NULL) { error = 1; goto finish_start; }
    /* set encoding */
    result = PyObject_CallFunction(set_encoding, "OOO", ud->parser, tag, attrs);
    if (result==NULL) { error=1; goto finish_start; }
    Py_DECREF(result); result = NULL;
    if (PyObject_HasAttrString(ud->handler, "start_element")==1) {
	callback = PyObject_GetAttrString(ud->handler, "start_element");
	if (!callback) { error=1; goto finish_start; }
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	if (!result) { error=1; goto finish_start; }
	Py_DECREF(callback);
        Py_DECREF(result);
        callback = result = NULL;
    }
    CHECK_ERROR(ud, finish_start);
finish_start:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 7:
#line 221 "htmlparse.y"
    {
    /* $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a PyDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM(yyvsp[0], 0);
    PyObject* attrs = PyTuple_GET_ITEM(yyvsp[0], 1);
    int error = 0;
    char* fname;
    PyObject* tagname;
    if (tag==NULL || attrs==NULL) { error = 1; goto finish_start_end; }
    tagname = PyUnicode_AsEncodedString(tag, "ascii", "ignore");
    if (tagname==NULL) { error=1; goto finish_start_end; }
    /* set encoding */
    result = PyObject_CallFunction(set_encoding, "OOO", ud->parser, tag, attrs);
    if (result==NULL) { error=1; goto finish_start_end; }
    Py_DECREF(result); result = NULL;
    if (html_end_tag(tagname, ud->parser))
        fname = "start_end_element";
    else
        fname = "start_element";
    if (PyObject_HasAttrString(ud->handler, fname)==1) {
	callback = PyObject_GetAttrString(ud->handler, fname);
	if (!callback) { error=1; goto finish_start_end; }
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	if (!result) { error=1; goto finish_start_end; }
	Py_DECREF(callback);
        Py_DECREF(result);
        callback = result = NULL;
    }
    CHECK_ERROR(ud, finish_start_end);
finish_start_end:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 8:
#line 268 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    /* encode tagname in ASCII, ignoring any unknown chars */
    PyObject* tagname = PyUnicode_AsEncodedString(yyvsp[0], "ascii", "ignore");
    if (tagname==NULL) { error=1; goto finish_end; }
    if (PyObject_HasAttrString(ud->handler, "end_element")==1 &&
	html_end_tag(tagname, ud->parser)) {
	callback = PyObject_GetAttrString(ud->handler, "end_element");
	if (callback==NULL) { error=1; goto finish_end; }
	result = PyObject_CallFunction(callback, "O", yyvsp[0]);
	if (result==NULL) { error=1; goto finish_end; }
	Py_DECREF(callback);
	Py_DECREF(result);
        callback = result = NULL;
    }
    CHECK_ERROR(ud, finish_end);
finish_end:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(tagname);
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 9:
#line 302 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "comment", "O", yyvsp[0], finish_comment);
    CHECK_ERROR(ud, finish_comment);
finish_comment:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 10:
#line 323 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "pi", "O", yyvsp[0], finish_pi);
    CHECK_ERROR(ud, finish_pi);
finish_pi:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 11:
#line 344 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "cdata", "O", yyvsp[0], finish_cdata);
    CHECK_ERROR(ud, finish_cdata);
finish_cdata:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 12:
#line 365 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    /* set encoding */
    result = PyObject_CallFunction(set_doctype, "OO", ud->parser, yyvsp[0]);
    if (result==NULL) { error=1; goto finish_doctype; }
    Py_DECREF(result); result = NULL;
    CALLBACK(ud, "doctype", "O", yyvsp[0], finish_doctype);
    CHECK_ERROR(ud, finish_doctype);
finish_doctype:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 13:
#line 390 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* script = PyUnicode_DecodeASCII("script", 6, "ignore");
    if (script==NULL) { error=1; goto finish_script; }
    CALLBACK(ud, "characters", "O", yyvsp[0], finish_script);
    CALLBACK(ud, "end_element", "O", script, finish_script);
    CHECK_ERROR(ud, finish_script);
finish_script:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(script);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 14:
#line 415 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* style = PyUnicode_DecodeASCII("style", 5, "ignore");
    if (style==NULL) { error=1; goto finish_style; }
    CALLBACK(ud, "characters", "O", yyvsp[0], finish_style);
    CALLBACK(ud, "end_element", "O", style, finish_style);
    CHECK_ERROR(ud, finish_style);
finish_style:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(style);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;

  case 15:
#line 440 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    /* Remember this is also called as a lexer error fallback */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", yyvsp[0], finish_characters);
    CHECK_ERROR(ud, finish_characters);
finish_characters:
    Py_XDECREF(ud->error);
    ud->error = NULL;
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF(yyvsp[0]);
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
;}
    break;


    }

/* Line 1010 of yacc.c.  */
#line 1481 "htmlparse.c"

  yyvsp -= yylen;
  yyssp -= yylen;


  YY_STACK_PRINT (yyss, yyssp);

  *++yyvsp = yyval;


  /* Now `shift' the result of the reduction.  Determine what state
     that goes to, based on the state we popped back to and the rule
     number reduced by.  */

  yyn = yyr1[yyn];

  yystate = yypgoto[yyn - YYNTOKENS] + *yyssp;
  if (0 <= yystate && yystate <= YYLAST && yycheck[yystate] == *yyssp)
    yystate = yytable[yystate];
  else
    yystate = yydefgoto[yyn - YYNTOKENS];

  goto yynewstate;


/*------------------------------------.
| yyerrlab -- here on detecting error |
`------------------------------------*/
yyerrlab:
  /* If not already recovering from an error, report this error.  */
  if (!yyerrstatus)
    {
      ++yynerrs;
#if YYERROR_VERBOSE
      yyn = yypact[yystate];

      if (YYPACT_NINF < yyn && yyn < YYLAST)
	{
	  YYSIZE_T yysize = 0;
	  int yytype = YYTRANSLATE (yychar);
	  const char* yyprefix;
	  char *yymsg;
	  int yyx;

	  /* Start YYX at -YYN if negative to avoid negative indexes in
	     YYCHECK.  */
	  int yyxbegin = yyn < 0 ? -yyn : 0;

	  /* Stay within bounds of both yycheck and yytname.  */
	  int yychecklim = YYLAST - yyn;
	  int yyxend = yychecklim < YYNTOKENS ? yychecklim : YYNTOKENS;
	  int yycount = 0;

	  yyprefix = ", expecting ";
	  for (yyx = yyxbegin; yyx < yyxend; ++yyx)
	    if (yycheck[yyx + yyn] == yyx && yyx != YYTERROR)
	      {
		yysize += yystrlen (yyprefix) + yystrlen (yytname [yyx]);
		yycount += 1;
		if (yycount == 5)
		  {
		    yysize = 0;
		    break;
		  }
	      }
	  yysize += (sizeof ("syntax error, unexpected ")
		     + yystrlen (yytname[yytype]));
	  yymsg = (char *) YYSTACK_ALLOC (yysize);
	  if (yymsg != 0)
	    {
	      char *yyp = yystpcpy (yymsg, "syntax error, unexpected ");
	      yyp = yystpcpy (yyp, yytname[yytype]);

	      if (yycount < 5)
		{
		  yyprefix = ", expecting ";
		  for (yyx = yyxbegin; yyx < yyxend; ++yyx)
		    if (yycheck[yyx + yyn] == yyx && yyx != YYTERROR)
		      {
			yyp = yystpcpy (yyp, yyprefix);
			yyp = yystpcpy (yyp, yytname[yyx]);
			yyprefix = " or ";
		      }
		}
	      yyerror (yymsg);
	      YYSTACK_FREE (yymsg);
	    }
	  else
	    yyerror ("syntax error; also virtual memory exhausted");
	}
      else
#endif /* YYERROR_VERBOSE */
	yyerror ("syntax error");
    }



  if (yyerrstatus == 3)
    {
      /* If just tried and failed to reuse lookahead token after an
	 error, discard it.  */

      if (yychar <= YYEOF)
        {
          /* If at end of input, pop the error token,
	     then the rest of the stack, then return failure.  */
	  if (yychar == YYEOF)
	     for (;;)
	       {
		 YYPOPSTACK;
		 if (yyssp == yyss)
		   YYABORT;
		 YYDSYMPRINTF ("Error: popping", yystos[*yyssp], yyvsp, yylsp);
		 yydestruct (yystos[*yyssp], yyvsp);
	       }
        }
      else
	{
	  YYDSYMPRINTF ("Error: discarding", yytoken, &yylval, &yylloc);
	  yydestruct (yytoken, &yylval);
	  yychar = YYEMPTY;

	}
    }

  /* Else will try to reuse lookahead token after shifting the error
     token.  */
  goto yyerrlab1;


/*---------------------------------------------------.
| yyerrorlab -- error raised explicitly by YYERROR.  |
`---------------------------------------------------*/
yyerrorlab:

#ifdef __GNUC__
  /* Pacify GCC when the user code never invokes YYERROR and the label
     yyerrorlab therefore never appears in user code.  */
  if (0)
     goto yyerrorlab;
#endif

  yyvsp -= yylen;
  yyssp -= yylen;
  yystate = *yyssp;
  goto yyerrlab1;


/*-------------------------------------------------------------.
| yyerrlab1 -- common code for both syntax error and YYERROR.  |
`-------------------------------------------------------------*/
yyerrlab1:
  yyerrstatus = 3;	/* Each real token shifted decrements this.  */

  for (;;)
    {
      yyn = yypact[yystate];
      if (yyn != YYPACT_NINF)
	{
	  yyn += YYTERROR;
	  if (0 <= yyn && yyn <= YYLAST && yycheck[yyn] == YYTERROR)
	    {
	      yyn = yytable[yyn];
	      if (0 < yyn)
		break;
	    }
	}

      /* Pop the current state because it cannot handle the error token.  */
      if (yyssp == yyss)
	YYABORT;

      YYDSYMPRINTF ("Error: popping", yystos[*yyssp], yyvsp, yylsp);
      yydestruct (yystos[yystate], yyvsp);
      YYPOPSTACK;
      yystate = *yyssp;
      YY_STACK_PRINT (yyss, yyssp);
    }

  if (yyn == YYFINAL)
    YYACCEPT;

  YYDPRINTF ((stderr, "Shifting error token, "));

  *++yyvsp = yylval;


  yystate = yyn;
  goto yynewstate;


/*-------------------------------------.
| yyacceptlab -- YYACCEPT comes here.  |
`-------------------------------------*/
yyacceptlab:
  yyresult = 0;
  goto yyreturn;

/*-----------------------------------.
| yyabortlab -- YYABORT comes here.  |
`-----------------------------------*/
yyabortlab:
  yyresult = 1;
  goto yyreturn;

#ifndef yyoverflow
/*----------------------------------------------.
| yyoverflowlab -- parser overflow comes here.  |
`----------------------------------------------*/
yyoverflowlab:
  yyerror ("parser stack overflow");
  yyresult = 2;
  /* Fall through.  */
#endif

yyreturn:
#ifndef yyoverflow
  if (yyss != yyssa)
    YYSTACK_FREE (yyss);
#endif
  return yyresult;
}


#line 463 "htmlparse.y"


/* create parser object */
static PyObject* parser_new (PyTypeObject* type, PyObject* args, PyObject* kwds) {
    parser_object* self;
    if ((self = (parser_object*) type->tp_alloc(type, 0)) == NULL) {
        return NULL;
    }
    Py_INCREF(Py_None);
    self->handler = Py_None;
    /* reset userData */
    self->userData = PyMem_New(UserData, sizeof(UserData));
    if (self->userData == NULL) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->userData->handler = self->handler;
    self->userData->buf = NULL;
    CLEAR_BUF_DECREF(self, self->userData->buf);
    self->userData->nextpos = 0;
    self->userData->bufpos = 0;
    self->userData->pos = 0;
    self->userData->column = 1;
    self->userData->last_column = 1;
    self->userData->lineno = 1;
    self->userData->last_lineno = 1;
    self->userData->tmp_buf = NULL;
    CLEAR_BUF_DECREF(self, self->userData->tmp_buf);
    self->userData->tmp_tag = self->userData->tmp_attrname =
        self->userData->tmp_attrval = self->userData->tmp_attrs =
        self->userData->lexbuf = NULL;
    self->userData->resolve_entities = resolve_entities;
    self->userData->list_dict = list_dict;
    self->userData->exc_type = NULL;
    self->userData->exc_val = NULL;
    self->userData->exc_tb = NULL;
    self->userData->error = NULL;
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->encoding = PyString_FromString("iso8859-1");
    if (self->encoding == NULL) {
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->doctype = PyString_FromString("HTML");
    if (self->doctype == NULL) {
        Py_DECREF(self->encoding);
        Py_DECREF(self->handler);
        Py_DECREF(self);
        return NULL;
    }
    self->userData->parser = (PyObject*)self;
    return (PyObject*) self;
}


/* initialize parser object */
static int parser_init (parser_object* self, PyObject* args, PyObject* kwds) {
    PyObject* handler = NULL;
    static char *kwlist[] = {"handler", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", kwlist, &handler)) {
        return -1;
    }
    if (handler==NULL) {
        return 0;
    }
    Py_DECREF(self->handler);
    Py_INCREF(handler);
    self->handler = handler;
    self->userData->handler = self->handler;
    return 0;
}


/* traverse all used subobjects participating in reference cycles */
static int parser_traverse (parser_object* self, visitproc visit, void* arg) {
    if (visit(self->handler, arg) < 0) {
        return -1;
    }
    return 0;
}


/* clear all used subobjects participating in reference cycles */
static int parser_clear (parser_object* self) {
    self->userData->handler = NULL;
    Py_XDECREF(self->handler);
    self->handler = NULL;
    return 0;
}


/* free all allocated resources of parser object */
static void parser_dealloc (parser_object* self) {
    htmllexDestroy(self->scanner);
    parser_clear(self);
    self->userData->parser = NULL;
    Py_XDECREF(self->encoding);
    self->encoding = NULL;
    Py_XDECREF(self->doctype);
    self->doctype = NULL;
    PyMem_Del(self->userData->buf);
    PyMem_Del(self->userData->tmp_buf);
    PyMem_Del(self->userData);
    self->ob_type->tp_free((PyObject*)self);
}


/* feed a chunk of data to the parser */
static PyObject* parser_feed (parser_object* self, PyObject* args) {
    /* set up the parse string */
    int slen = 0;
    char* s = NULL;
    if (!PyArg_ParseTuple(args, "t#", &s, &slen)) {
	PyErr_SetString(PyExc_TypeError, "string arg required");
	return NULL;
    }
    /* parse */
    if (htmllexStart(self->scanner, self->userData, s, slen)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not start scanner");
 	return NULL;
    }
    if (yyparse(self->scanner)!=0) {
        if (self->userData->exc_type!=NULL) {
            /* note: we give away these objects, so don't decref */
            PyErr_Restore(self->userData->exc_type,
        		  self->userData->exc_val,
        		  self->userData->exc_tb);
        }
        htmllexStop(self->scanner, self->userData);
        return NULL;
    }
    if (htmllexStop(self->scanner, self->userData)!=0) {
	PyErr_SetString(PyExc_MemoryError, "could not stop scanner");
	return NULL;
    }
    Py_RETURN_NONE;
}


/* flush all parser buffers */
static PyObject* parser_flush (parser_object* self, PyObject* args) {
    int res = 0;
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    /* reset parser variables */
    CLEAR_BUF(self->userData->tmp_buf);
    Py_XDECREF(self->userData->tmp_tag);
    Py_XDECREF(self->userData->tmp_attrs);
    Py_XDECREF(self->userData->tmp_attrval);
    Py_XDECREF(self->userData->tmp_attrname);
    self->userData->tmp_tag = self->userData->tmp_attrs =
	self->userData->tmp_attrval = self->userData->tmp_attrname = NULL;
    self->userData->bufpos = 0;
    if (strlen(self->userData->buf)) {
        /* XXX set line, col */
        int error = 0;
        const char* enc = PyString_AsString(self->encoding);
	PyObject* s = PyUnicode_Decode(self->userData->buf,
                                       strlen(self->userData->buf),
                                       enc, "ignore");
	PyObject* callback = NULL;
	PyObject* result = NULL;
	/* reset buffer */
	CLEAR_BUF(self->userData->buf);
	if (s==NULL) { error=1; goto finish_flush; }
	if (PyObject_HasAttrString(self->handler, "characters")==1) {
	    callback = PyObject_GetAttrString(self->handler, "characters");
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
    if (htmllexDestroy(self->scanner)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not destroy scanner data");
        return NULL;
    }
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not initialize scanner data");
        return NULL;
    }
    return Py_BuildValue("i", res);
}


/* return the current parser line number */
static PyObject* parser_lineno (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->lineno);
}


/* return the last parser line number */
static PyObject* parser_last_lineno (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->last_lineno);
}


/* return the current parser column number */
static PyObject* parser_column (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->column);
}


/* return the last parser column number */
static PyObject* parser_last_column (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->last_column);
}


/* return the parser position in data stream */
static PyObject* parser_pos (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
        return NULL;
    }
    return Py_BuildValue("i", self->userData->pos);
}


/* reset the parser. This will erase all buffered data! */
static PyObject* parser_reset (parser_object* self, PyObject* args) {
    if (!PyArg_ParseTuple(args, "")) {
	PyErr_SetString(PyExc_TypeError, "no args required");
	return NULL;
    }
    if (htmllexDestroy(self->scanner)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not destroy scanner data");
        return NULL;
    }
    /* reset buffer */
    CLEAR_BUF(self->userData->buf);
    CLEAR_BUF(self->userData->tmp_buf);
    self->userData->bufpos =
        self->userData->pos =
        self->userData->nextpos = 0;
    self->userData->column =
	self->userData->last_column =
	self->userData->lineno =
	self->userData->last_lineno = 1;
    self->userData->tmp_tag = self->userData->tmp_attrs =
        self->userData->tmp_attrval = self->userData->tmp_attrname = NULL;
    self->scanner = NULL;
    if (htmllexInit(&(self->scanner), self->userData)!=0) {
        PyErr_SetString(PyExc_MemoryError, "could not initialize scanner data");
        return NULL;
    }
    Py_RETURN_NONE;
}


/* set the debug level, if its >0, debugging is on, =0 means off */
static PyObject* parser_debug (parser_object* self, PyObject* args) {
    int debug;
    if (!PyArg_ParseTuple(args, "i", &debug)) {
        return NULL;
    }
    yydebug = debug;
    debug = htmllexDebug(&(self->scanner), debug);
    return PyInt_FromLong((long)debug);
}


static PyObject* parser_gethandler (parser_object* self, void* closure) {
    Py_INCREF(self->handler);
    return self->handler;
}


static int parser_sethandler (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
       PyErr_SetString(PyExc_TypeError, "Cannot delete parser handler");
       return -1;
    }
    Py_DECREF(self->handler);
    Py_INCREF(value);
    self->handler = value;
    self->userData->handler = value;
    return 0;
}


static PyObject* parser_getencoding (parser_object* self, void* closure) {
    Py_INCREF(self->encoding);
    return self->encoding;
}


static int parser_setencoding (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete encoding");
        return -1;
    }
    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "encoding must be string");
        return -1;
    }
    Py_DECREF(self->encoding);
    Py_INCREF(value);
    self->encoding = value;
    return 0;
}


static PyObject* parser_getdoctype (parser_object* self, void* closure) {
    Py_INCREF(self->doctype);
    return self->doctype;
}


static int parser_setdoctype (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete doctype");
        return -1;
    }
    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "doctype must be string");
        return -1;
    }
    Py_DECREF(self->doctype);
    Py_INCREF(value);
    self->doctype = value;
    return 0;
}


/* type interface */

static PyMemberDef parser_members[] = {
    {NULL}  /* Sentinel */
};

static PyGetSetDef parser_getset[] = {
    {"handler", (getter)parser_gethandler, (setter)parser_sethandler,
     "handler object", NULL},
    {"encoding", (getter)parser_getencoding, (setter)parser_setencoding,
     "encoding", NULL},
    {"doctype", (getter)parser_getdoctype, (setter)parser_setdoctype,
     "doctype", NULL},
    {NULL}  /* Sentinel */
};

static PyMethodDef parser_methods[] = {
    {"feed", (PyCFunction)parser_feed, METH_VARARGS, "feed data to parse incremental"},
    {"reset", (PyCFunction)parser_reset, METH_VARARGS, "reset the parser (no flushing)"},
    {"flush", (PyCFunction)parser_flush, METH_VARARGS, "flush parser buffers"},
    {"debug", (PyCFunction)parser_debug, METH_VARARGS, "set debug level"},
    {"lineno", (PyCFunction)parser_lineno, METH_VARARGS, "get the current line number"},
    {"last_lineno", (PyCFunction)parser_last_lineno, METH_VARARGS, "get the last line number"},
    {"column", (PyCFunction)parser_column, METH_VARARGS, "get the current column"},
    {"last_column", (PyCFunction)parser_last_column, METH_VARARGS, "get the last column"},
    {"pos", (PyCFunction)parser_pos, METH_VARARGS, "get the current scanner position"},
    {NULL} /* Sentinel */
};


static PyTypeObject parser_type = {
    PyObject_HEAD_INIT(NULL)
    0,              /* ob_size */
    "linkcheck.HtmlParser.htmlsax.parser",      /* tp_name */
    sizeof(parser_object), /* tp_size */
    0,              /* tp_itemsize */
    /* methods */
    (destructor)parser_dealloc, /* tp_dealloc */
    0,              /* tp_print */
    0,              /* tp_getattr */
    0,              /* tp_setattr */
    0,              /* tp_compare */
    0,              /* tp_repr */
    0,              /* tp_as_number */
    0,              /* tp_as_sequence */
    0,              /* tp_as_mapping */
    0,              /* tp_hash */
    0,              /* tp_call */
    0,              /* tp_str */
    0,              /* tp_getattro */
    0,              /* tp_setattro */
    0,              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | 
      Py_TPFLAGS_HAVE_GC, /* tp_flags */
    "HTML parser object", /* tp_doc */
    (traverseproc)parser_traverse, /* tp_traverse */
    (inquiry)parser_clear, /* tp_clear */
    0,              /* tp_richcompare */
    0,              /* tp_weaklistoffset */
    0,              /* tp_iter */
    0,              /* tp_iternext */
    parser_methods, /* tp_methods */
    parser_members, /* tp_members */
    parser_getset,  /* tp_getset */
    0,              /* tp_base */
    0,              /* tp_dict */
    0,              /* tp_descr_get */
    0,              /* tp_descr_set */
    0,              /* tp_dictoffset */
    (initproc)parser_init,  /* tp_init */
    0,              /* tp_alloc */
    parser_new,     /* tp_new */
    0,              /* tp_free */
    0,              /* tp_is_gc */
    0,              /* tp_bases */
    0,              /* tp_mro */
    0,              /* tp_cache */
    0,              /* tp_subclasses */
    0,              /* tp_weaklist */
    0,              /* tp_del */
};


/* python module interface 
     "Create a new HTML parser object with handler (which may be None).\n"
     "\n"
     "Used callbacks (they don't have to be defined) of a handler are:\n"
     "comment(data): <!--data-->\n"
     "start_element(tag, attrs): <tag {attr1:value1,attr2:value2,..}>\n"
     "end_element(tag): </tag>\n"
     "doctype(data): <!DOCTYPE data?>\n"
     "pi(name, data=None): <?name data?>\n"
     "cdata(data): <![CDATA[data]]>\n"
     "characters(data): data\n"
     "\n"
     "Additionally, there are error and warning callbacks:\n"
     "error(msg)\n"
     "warning(msg)\n"
     "fatal_error(msg)\n"},

*/

static PyMethodDef htmlsax_methods[] = {
    {NULL} /* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
/* initialization of the htmlsax module */
PyMODINIT_FUNC inithtmlsax (void) {
    PyObject* m = NULL;
    if (PyType_Ready(&parser_type) < 0) {
        return;
    }
    if ((m = Py_InitModule3("htmlsax", htmlsax_methods, "SAX HTML parser routines"))==NULL) {
        return;
    }
    Py_INCREF(&parser_type);
    if (PyModule_AddObject(m, "parser", (PyObject *)&parser_type)==-1) {
        /* init error */
        PyErr_Print();
    }
    if ((m = PyImport_ImportModule("linkcheck.HtmlParser"))==NULL) {
        return;
    }
    if ((resolve_entities = PyObject_GetAttrString(m, "resolve_entities"))==NULL) {
        Py_DECREF(m);
        return;
    }
    if ((set_encoding = PyObject_GetAttrString(m, "set_encoding"))==NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(m);
        return;
    }
    if ((set_doctype = PyObject_GetAttrString(m, "set_doctype"))==NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(set_encoding);
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
    if ((m = PyImport_ImportModule("linkcheck.containers"))==NULL) {
        return;
    }
    if ((list_dict = PyObject_GetAttrString(m, "ListDict"))==NULL) {
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
}

