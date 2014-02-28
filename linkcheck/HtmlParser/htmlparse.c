/* A Bison parser, made by GNU Bison 2.5.  */

/* Bison implementation for Yacc-like parsers in C
   
      Copyright (C) 1984, 1989-1990, 2000-2011 Free Software Foundation, Inc.
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.
   
   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* C LALR(1) parser skeleton written by Richard Stallman, by
   simplifying the original so-called "semantic" parser.  */

/* All symbols defined below should begin with yy or YY, to avoid
   infringing on user name space.  This should be done even for local
   variables, as they might otherwise be expanded by user macros.
   There are some unavoidable exceptions within include files to
   define necessary library symbols; they are noted "INFRINGES ON
   USER NAME SPACE" below.  */

/* Identify Bison output.  */
#define YYBISON 1

/* Bison version.  */
#define YYBISON_VERSION "2.5"

/* Skeleton name.  */
#define YYSKELETON_NAME "yacc.c"

/* Pure parsers.  */
#define YYPURE 1

/* Push parsers.  */
#define YYPUSH 0

/* Pull parsers.  */
#define YYPULL 1

/* Using locations.  */
#define YYLSP_NEEDED 0



/* Copy the first part of user declarations.  */

/* Line 268 of yacc.c  */
#line 1 "htmlparse.y"

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
/* A SAX HTML parser. Includes Python module definition to make it
   usable for Python programs.
*/
#include "htmlsax.h"      /* SAX interface (includes Python.h) */
#include "structmember.h" /* Python include for object definition */
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
extern UserData* yyget_extra(void* scanner);
extern int yyget_lineno(void*);
#define YYERROR_VERBOSE 1

/* standard error reporting, indicating an internal error */
static int yyerror (char* msg) {
    fprintf(stderr, "htmlsax: internal parse error: %s\n", msg);
    return 0;
}

/* existing Python methods */

/* parser.resolve_entities */
static PyObject* resolve_entities;
/* ListDict class, sorted dictionary */
static PyObject* list_dict;
/* set_encoding helper function */
static PyObject* set_encoding;
/* set_doctype helper function */
static PyObject* set_doctype;
/* the unicode string u'meta' */
static PyObject* u_meta;

/* macros for easier scanner state manipulation */

/* clear buffer b, returning NULL on error */
#define CLEAR_BUF(b) \
    b = PyMem_Resize(b, char, 1); \
    if (b == NULL) return NULL; \
    (b)[0] = '\0'

/* clear buffer b, returning NULL and decref self on error */
#define CLEAR_BUF_DECREF(self, b) \
    b = PyMem_Resize(b, char, 1); \
    if (b == NULL) { Py_DECREF(self); return NULL; } \
    (b)[0] = '\0'

/* check an error condition and if true set error flag and goto given label */
#define CHECK_ERROR(cond, label) \
    if (cond) { \
        error = 1; \
        goto label; \
    }

/* generic Python callback macro */
#define CALLBACK(ud, attr, format, arg, label) \
    if (PyObject_HasAttrString(ud->handler, attr) == 1) { \
	callback = PyObject_GetAttrString(ud->handler, attr); \
	CHECK_ERROR((callback == NULL), label); \
	result = PyObject_CallFunction(callback, format, arg); \
	CHECK_ERROR((result == NULL), label); \
	Py_CLEAR(callback); \
	Py_CLEAR(result); \
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

/* use Pythons memory management */
#define YYMALLOC PyMem_Malloc
#define YYFREE PyMem_Free

/* Test whether tag does not need an HTML end tag.
   @ptag: ASCII encoded Python string in lowercase (!)
   @parser: SAX parser object
   @return: < 0 on error, > 0 if HTML end tag is needed, else 0
*/
static int html_end_tag (PyObject* ptag, PyObject* parser) {
    PyObject* pdoctype = NULL;
    char* doctype;
    int error = 0;
    int ret = 1;
    pdoctype = PyObject_GetAttrString(parser, "doctype");
    CHECK_ERROR((pdoctype == NULL), finish_html_end_tag);
    doctype = PyString_AsString(pdoctype);
    CHECK_ERROR((doctype == NULL), finish_html_end_tag);
    /* check for HTML (else it's presumably XHTML) */
    if (strcmp(doctype, "HTML") == 0) {
        char* tag = PyString_AsString(ptag);
        CHECK_ERROR((tag == NULL), finish_html_end_tag);
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
finish_html_end_tag:
    Py_XDECREF(pdoctype);
    if (error) {
        return -1;
    }
    return ret;
}



/* Line 268 of yacc.c  */
#line 227 "htmlparse.c"

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

/* Enabling the token table.  */
#ifndef YYTOKEN_TABLE
# define YYTOKEN_TABLE 0
#endif


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



#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
typedef int YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define yystype YYSTYPE /* obsolescent; will be withdrawn */
# define YYSTYPE_IS_DECLARED 1
#endif


/* Copy the second part of user declarations.  */


/* Line 343 of yacc.c  */
#line 283 "htmlparse.c"

#ifdef short
# undef short
#endif

#ifdef YYTYPE_UINT8
typedef YYTYPE_UINT8 yytype_uint8;
#else
typedef unsigned char yytype_uint8;
#endif

#ifdef YYTYPE_INT8
typedef YYTYPE_INT8 yytype_int8;
#elif (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
typedef signed char yytype_int8;
#else
typedef short int yytype_int8;
#endif

#ifdef YYTYPE_UINT16
typedef YYTYPE_UINT16 yytype_uint16;
#else
typedef unsigned short int yytype_uint16;
#endif

#ifdef YYTYPE_INT16
typedef YYTYPE_INT16 yytype_int16;
#else
typedef short int yytype_int16;
#endif

#ifndef YYSIZE_T
# ifdef __SIZE_TYPE__
#  define YYSIZE_T __SIZE_TYPE__
# elif defined size_t
#  define YYSIZE_T size_t
# elif ! defined YYSIZE_T && (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
#  include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  define YYSIZE_T size_t
# else
#  define YYSIZE_T unsigned int
# endif
#endif

#define YYSIZE_MAXIMUM ((YYSIZE_T) -1)

#ifndef YY_
# if defined YYENABLE_NLS && YYENABLE_NLS
#  if ENABLE_NLS
#   include <libintl.h> /* INFRINGES ON USER NAME SPACE */
#   define YY_(msgid) dgettext ("bison-runtime", msgid)
#  endif
# endif
# ifndef YY_
#  define YY_(msgid) msgid
# endif
#endif

/* Suppress unused-variable warnings by "using" E.  */
#if ! defined lint || defined __GNUC__
# define YYUSE(e) ((void) (e))
#else
# define YYUSE(e) /* empty */
#endif

/* Identity function, used to suppress warnings about constant conditions.  */
#ifndef lint
# define YYID(n) (n)
#else
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static int
YYID (int yyi)
#else
static int
YYID (yyi)
    int yyi;
#endif
{
  return yyi;
}
#endif

#if ! defined yyoverflow || YYERROR_VERBOSE

/* The parser invokes alloca or malloc; define the necessary symbols.  */

# ifdef YYSTACK_USE_ALLOCA
#  if YYSTACK_USE_ALLOCA
#   ifdef __GNUC__
#    define YYSTACK_ALLOC __builtin_alloca
#   elif defined __BUILTIN_VA_ARG_INCR
#    include <alloca.h> /* INFRINGES ON USER NAME SPACE */
#   elif defined _AIX
#    define YYSTACK_ALLOC __alloca
#   elif defined _MSC_VER
#    include <malloc.h> /* INFRINGES ON USER NAME SPACE */
#    define alloca _alloca
#   else
#    define YYSTACK_ALLOC alloca
#    if ! defined _ALLOCA_H && ! defined EXIT_SUCCESS && (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
#     include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#     ifndef EXIT_SUCCESS
#      define EXIT_SUCCESS 0
#     endif
#    endif
#   endif
#  endif
# endif

# ifdef YYSTACK_ALLOC
   /* Pacify GCC's `empty if-body' warning.  */
#  define YYSTACK_FREE(Ptr) do { /* empty */; } while (YYID (0))
#  ifndef YYSTACK_ALLOC_MAXIMUM
    /* The OS might guarantee only one guard page at the bottom of the stack,
       and a page size can be as small as 4096 bytes.  So we cannot safely
       invoke alloca (N) if N exceeds 4096.  Use a slightly smaller number
       to allow for a few compiler-allocated temporary stack slots.  */
#   define YYSTACK_ALLOC_MAXIMUM 4032 /* reasonable circa 2006 */
#  endif
# else
#  define YYSTACK_ALLOC YYMALLOC
#  define YYSTACK_FREE YYFREE
#  ifndef YYSTACK_ALLOC_MAXIMUM
#   define YYSTACK_ALLOC_MAXIMUM YYSIZE_MAXIMUM
#  endif
#  if (defined __cplusplus && ! defined EXIT_SUCCESS \
       && ! ((defined YYMALLOC || defined malloc) \
	     && (defined YYFREE || defined free)))
#   include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#   ifndef EXIT_SUCCESS
#    define EXIT_SUCCESS 0
#   endif
#  endif
#  ifndef YYMALLOC
#   define YYMALLOC malloc
#   if ! defined malloc && ! defined EXIT_SUCCESS && (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
void *malloc (YYSIZE_T); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
#  ifndef YYFREE
#   define YYFREE free
#   if ! defined free && ! defined EXIT_SUCCESS && (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
void free (void *); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
# endif
#endif /* ! defined yyoverflow || YYERROR_VERBOSE */


#if (! defined yyoverflow \
     && (! defined __cplusplus \
	 || (defined YYSTYPE_IS_TRIVIAL && YYSTYPE_IS_TRIVIAL)))

/* A type that is properly aligned for any stack member.  */
union yyalloc
{
  yytype_int16 yyss_alloc;
  YYSTYPE yyvs_alloc;
};

/* The size of the maximum gap between one aligned stack and the next.  */
# define YYSTACK_GAP_MAXIMUM (sizeof (union yyalloc) - 1)

/* The size of an array large to enough to hold all stacks, each with
   N elements.  */
# define YYSTACK_BYTES(N) \
     ((N) * (sizeof (yytype_int16) + sizeof (YYSTYPE)) \
      + YYSTACK_GAP_MAXIMUM)

# define YYCOPY_NEEDED 1

/* Relocate STACK from its old location to the new one.  The
   local variables YYSIZE and YYSTACKSIZE give the old and new number of
   elements in the stack, and YYPTR gives the new location of the
   stack.  Advance YYPTR to a properly aligned location for the next
   stack.  */
# define YYSTACK_RELOCATE(Stack_alloc, Stack)				\
    do									\
      {									\
	YYSIZE_T yynewbytes;						\
	YYCOPY (&yyptr->Stack_alloc, Stack, yysize);			\
	Stack = &yyptr->Stack_alloc;					\
	yynewbytes = yystacksize * sizeof (*Stack) + YYSTACK_GAP_MAXIMUM; \
	yyptr += yynewbytes / sizeof (*yyptr);				\
      }									\
    while (YYID (0))

#endif

#if defined YYCOPY_NEEDED && YYCOPY_NEEDED
/* Copy COUNT objects from FROM to TO.  The source and destination do
   not overlap.  */
# ifndef YYCOPY
#  if defined __GNUC__ && 1 < __GNUC__
#   define YYCOPY(To, From, Count) \
      __builtin_memcpy (To, From, (Count) * sizeof (*(From)))
#  else
#   define YYCOPY(To, From, Count)		\
      do					\
	{					\
	  YYSIZE_T yyi;				\
	  for (yyi = 0; yyi < (Count); yyi++)	\
	    (To)[yyi] = (From)[yyi];		\
	}					\
      while (YYID (0))
#  endif
# endif
#endif /* !YYCOPY_NEEDED */

/* YYFINAL -- State number of the termination state.  */
#define YYFINAL  15
/* YYLAST -- Last index in YYTABLE.  */
#define YYLAST   26

/* YYNTOKENS -- Number of terminals.  */
#define YYNTOKENS  15
/* YYNNTS -- Number of nonterminals.  */
#define YYNNTS  3
/* YYNRULES -- Number of rules.  */
#define YYNRULES  15
/* YYNRULES -- Number of states.  */
#define YYNSTATES  17

/* YYTRANSLATE(YYLEX) -- Bison symbol number corresponding to YYLEX.  */
#define YYUNDEFTOK  2
#define YYMAXUTOK   269

#define YYTRANSLATE(YYX)						\
  ((unsigned int) (YYX) <= YYMAXUTOK ? yytranslate[YYX] : YYUNDEFTOK)

/* YYTRANSLATE[YYLEX] -- Bison symbol number corresponding to YYLEX.  */
static const yytype_uint8 yytranslate[] =
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
static const yytype_uint8 yyprhs[] =
{
       0,     0,     3,     5,     8,    10,    12,    14,    16,    18,
      20,    22,    24,    26,    28,    30
};

/* YYRHS -- A `-1'-separated list of the rules' RHS.  */
static const yytype_int8 yyrhs[] =
{
      16,     0,    -1,    17,    -1,    16,    17,    -1,     3,    -1,
       4,    -1,     6,    -1,     7,    -1,     8,    -1,    12,    -1,
      11,    -1,    13,    -1,    14,    -1,     9,    -1,    10,    -1,
       5,    -1
};

/* YYRLINE[YYN] -- source line where rule number YYN was defined.  */
static const yytype_uint16 yyrline[] =
{
       0,   180,   180,   183,   188,   192,   199,   240,   288,   324,
     343,   361,   380,   403,   427,   451
};
#endif

#if YYDEBUG || YYERROR_VERBOSE || YYTOKEN_TABLE
/* YYTNAME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
   First, the terminals, then, starting at YYNTOKENS, nonterminals.  */
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
static const yytype_uint16 yytoknum[] =
{
       0,   256,   257,   258,   259,   260,   261,   262,   263,   264,
     265,   266,   267,   268,   269
};
# endif

/* YYR1[YYN] -- Symbol number of symbol that rule YYN derives.  */
static const yytype_uint8 yyr1[] =
{
       0,    15,    16,    16,    17,    17,    17,    17,    17,    17,
      17,    17,    17,    17,    17,    17
};

/* YYR2[YYN] -- Number of symbols composing right hand side of rule YYN.  */
static const yytype_uint8 yyr2[] =
{
       0,     2,     1,     2,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     1,     1,     1
};

/* YYDEFACT[STATE-NAME] -- Default reduction number in state STATE-NUM.
   Performed when YYTABLE doesn't specify something else to do.  Zero
   means the default is an error.  */
static const yytype_uint8 yydefact[] =
{
       0,     4,     5,    15,     6,     7,     8,    13,    14,    10,
       9,    11,    12,     0,     2,     1,     3
};

/* YYDEFGOTO[NTERM-NUM].  */
static const yytype_int8 yydefgoto[] =
{
      -1,    13,    14
};

/* YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
   STATE-NUM.  */
#define YYPACT_NINF -13
static const yytype_int8 yypact[] =
{
      12,   -13,   -13,   -13,   -13,   -13,   -13,   -13,   -13,   -13,
     -13,   -13,   -13,     0,   -13,   -13,   -13
};

/* YYPGOTO[NTERM-NUM].  */
static const yytype_int8 yypgoto[] =
{
     -13,   -13,   -12
};

/* YYTABLE[YYPACT[STATE-NUM]].  What to do in state STATE-NUM.  If
   positive, shift that token.  If negative, reduce the rule which
   number is the opposite.  If YYTABLE_NINF, syntax error.  */
#define YYTABLE_NINF -1
static const yytype_uint8 yytable[] =
{
      15,    16,     0,     1,     2,     3,     4,     5,     6,     7,
       8,     9,    10,    11,    12,     1,     2,     3,     4,     5,
       6,     7,     8,     9,    10,    11,    12
};

#define yypact_value_is_default(yystate) \
  ((yystate) == (-13))

#define yytable_value_is_error(yytable_value) \
  YYID (0)

static const yytype_int8 yycheck[] =
{
       0,    13,    -1,     3,     4,     5,     6,     7,     8,     9,
      10,    11,    12,    13,    14,     3,     4,     5,     6,     7,
       8,     9,    10,    11,    12,    13,    14
};

/* YYSTOS[STATE-NUM] -- The (internal number of the) accessing
   symbol of state STATE-NUM.  */
static const yytype_uint8 yystos[] =
{
       0,     3,     4,     5,     6,     7,     8,     9,    10,    11,
      12,    13,    14,    16,    17,     0,    17
};

#define yyerrok		(yyerrstatus = 0)
#define yyclearin	(yychar = YYEMPTY)
#define YYEMPTY		(-2)
#define YYEOF		0

#define YYACCEPT	goto yyacceptlab
#define YYABORT		goto yyabortlab
#define YYERROR		goto yyerrorlab


/* Like YYERROR except do call yyerror.  This remains here temporarily
   to ease the transition to the new meaning of YYERROR, for GCC.
   Once GCC version 2 has supplanted version 1, this can go.  However,
   YYFAIL appears to be in use.  Nevertheless, it is formally deprecated
   in Bison 2.4.2's NEWS entry, where a plan to phase it out is
   discussed.  */

#define YYFAIL		goto yyerrlab
#if defined YYFAIL
  /* This is here to suppress warnings from the GCC cpp's
     -Wunused-macros.  Normally we don't worry about that warning, but
     some users do, and we want to make it easy for users to remove
     YYFAIL uses, which will produce warnings from Bison 2.5.  */
#endif

#define YYRECOVERING()  (!!yyerrstatus)

#define YYBACKUP(Token, Value)					\
do								\
  if (yychar == YYEMPTY && yylen == 1)				\
    {								\
      yychar = (Token);						\
      yylval = (Value);						\
      YYPOPSTACK (1);						\
      goto yybackup;						\
    }								\
  else								\
    {								\
      yyerror (YY_("syntax error: cannot back up")); \
      YYERROR;							\
    }								\
while (YYID (0))


#define YYTERROR	1
#define YYERRCODE	256


/* YYLLOC_DEFAULT -- Set CURRENT to span from RHS[1] to RHS[N].
   If N is 0, then set CURRENT to the empty location which ends
   the previous symbol: RHS[0] (always defined).  */

#define YYRHSLOC(Rhs, K) ((Rhs)[K])
#ifndef YYLLOC_DEFAULT
# define YYLLOC_DEFAULT(Current, Rhs, N)				\
    do									\
      if (YYID (N))                                                    \
	{								\
	  (Current).first_line   = YYRHSLOC (Rhs, 1).first_line;	\
	  (Current).first_column = YYRHSLOC (Rhs, 1).first_column;	\
	  (Current).last_line    = YYRHSLOC (Rhs, N).last_line;		\
	  (Current).last_column  = YYRHSLOC (Rhs, N).last_column;	\
	}								\
      else								\
	{								\
	  (Current).first_line   = (Current).last_line   =		\
	    YYRHSLOC (Rhs, 0).last_line;				\
	  (Current).first_column = (Current).last_column =		\
	    YYRHSLOC (Rhs, 0).last_column;				\
	}								\
    while (YYID (0))
#endif


/* This macro is provided for backward compatibility. */

#ifndef YY_LOCATION_PRINT
# define YY_LOCATION_PRINT(File, Loc) ((void) 0)
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
} while (YYID (0))

# define YY_SYMBOL_PRINT(Title, Type, Value, Location)			  \
do {									  \
  if (yydebug)								  \
    {									  \
      YYFPRINTF (stderr, "%s ", Title);					  \
      yy_symbol_print (stderr,						  \
		  Type, Value); \
      YYFPRINTF (stderr, "\n");						  \
    }									  \
} while (YYID (0))


/*--------------------------------.
| Print this symbol on YYOUTPUT.  |
`--------------------------------*/

/*ARGSUSED*/
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static void
yy_symbol_value_print (FILE *yyoutput, int yytype, YYSTYPE const * const yyvaluep)
#else
static void
yy_symbol_value_print (yyoutput, yytype, yyvaluep)
    FILE *yyoutput;
    int yytype;
    YYSTYPE const * const yyvaluep;
#endif
{
  if (!yyvaluep)
    return;
# ifdef YYPRINT
  if (yytype < YYNTOKENS)
    YYPRINT (yyoutput, yytoknum[yytype], *yyvaluep);
# else
  YYUSE (yyoutput);
# endif
  switch (yytype)
    {
      default:
	break;
    }
}


/*--------------------------------.
| Print this symbol on YYOUTPUT.  |
`--------------------------------*/

#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static void
yy_symbol_print (FILE *yyoutput, int yytype, YYSTYPE const * const yyvaluep)
#else
static void
yy_symbol_print (yyoutput, yytype, yyvaluep)
    FILE *yyoutput;
    int yytype;
    YYSTYPE const * const yyvaluep;
#endif
{
  if (yytype < YYNTOKENS)
    YYFPRINTF (yyoutput, "token %s (", yytname[yytype]);
  else
    YYFPRINTF (yyoutput, "nterm %s (", yytname[yytype]);

  yy_symbol_value_print (yyoutput, yytype, yyvaluep);
  YYFPRINTF (yyoutput, ")");
}

/*------------------------------------------------------------------.
| yy_stack_print -- Print the state stack from its BOTTOM up to its |
| TOP (included).                                                   |
`------------------------------------------------------------------*/

#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static void
yy_stack_print (yytype_int16 *yybottom, yytype_int16 *yytop)
#else
static void
yy_stack_print (yybottom, yytop)
    yytype_int16 *yybottom;
    yytype_int16 *yytop;
#endif
{
  YYFPRINTF (stderr, "Stack now");
  for (; yybottom <= yytop; yybottom++)
    {
      int yybot = *yybottom;
      YYFPRINTF (stderr, " %d", yybot);
    }
  YYFPRINTF (stderr, "\n");
}

# define YY_STACK_PRINT(Bottom, Top)				\
do {								\
  if (yydebug)							\
    yy_stack_print ((Bottom), (Top));				\
} while (YYID (0))


/*------------------------------------------------.
| Report that the YYRULE is going to be reduced.  |
`------------------------------------------------*/

#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static void
yy_reduce_print (YYSTYPE *yyvsp, int yyrule)
#else
static void
yy_reduce_print (yyvsp, yyrule)
    YYSTYPE *yyvsp;
    int yyrule;
#endif
{
  int yynrhs = yyr2[yyrule];
  int yyi;
  unsigned long int yylno = yyrline[yyrule];
  YYFPRINTF (stderr, "Reducing stack by rule %d (line %lu):\n",
	     yyrule - 1, yylno);
  /* The symbols being reduced.  */
  for (yyi = 0; yyi < yynrhs; yyi++)
    {
      YYFPRINTF (stderr, "   $%d = ", yyi + 1);
      yy_symbol_print (stderr, yyrhs[yyprhs[yyrule] + yyi],
		       &(yyvsp[(yyi + 1) - (yynrhs)])
		       		       );
      YYFPRINTF (stderr, "\n");
    }
}

# define YY_REDUCE_PRINT(Rule)		\
do {					\
  if (yydebug)				\
    yy_reduce_print (yyvsp, Rule); \
} while (YYID (0))

/* Nonzero means print parse trace.  It is left uninitialized so that
   multiple parsers can coexist.  */
int yydebug;
#else /* !YYDEBUG */
# define YYDPRINTF(Args)
# define YY_SYMBOL_PRINT(Title, Type, Value, Location)
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
   YYSTACK_ALLOC_MAXIMUM < YYSTACK_BYTES (YYMAXDEPTH)
   evaluated with infinite-precision integer arithmetic.  */

#ifndef YYMAXDEPTH
# define YYMAXDEPTH 10000
#endif


#if YYERROR_VERBOSE

# ifndef yystrlen
#  if defined __GLIBC__ && defined _STRING_H
#   define yystrlen strlen
#  else
/* Return the length of YYSTR.  */
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static YYSIZE_T
yystrlen (const char *yystr)
#else
static YYSIZE_T
yystrlen (yystr)
    const char *yystr;
#endif
{
  YYSIZE_T yylen;
  for (yylen = 0; yystr[yylen]; yylen++)
    continue;
  return yylen;
}
#  endif
# endif

# ifndef yystpcpy
#  if defined __GLIBC__ && defined _STRING_H && defined _GNU_SOURCE
#   define yystpcpy stpcpy
#  else
/* Copy YYSRC to YYDEST, returning the address of the terminating '\0' in
   YYDEST.  */
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static char *
yystpcpy (char *yydest, const char *yysrc)
#else
static char *
yystpcpy (yydest, yysrc)
    char *yydest;
    const char *yysrc;
#endif
{
  char *yyd = yydest;
  const char *yys = yysrc;

  while ((*yyd++ = *yys++) != '\0')
    continue;

  return yyd - 1;
}
#  endif
# endif

# ifndef yytnamerr
/* Copy to YYRES the contents of YYSTR after stripping away unnecessary
   quotes and backslashes, so that it's suitable for yyerror.  The
   heuristic is that double-quoting is unnecessary unless the string
   contains an apostrophe, a comma, or backslash (other than
   backslash-backslash).  YYSTR is taken from yytname.  If YYRES is
   null, do not copy; instead, return the length of what the result
   would have been.  */
static YYSIZE_T
yytnamerr (char *yyres, const char *yystr)
{
  if (*yystr == '"')
    {
      YYSIZE_T yyn = 0;
      char const *yyp = yystr;

      for (;;)
	switch (*++yyp)
	  {
	  case '\'':
	  case ',':
	    goto do_not_strip_quotes;

	  case '\\':
	    if (*++yyp != '\\')
	      goto do_not_strip_quotes;
	    /* Fall through.  */
	  default:
	    if (yyres)
	      yyres[yyn] = *yyp;
	    yyn++;
	    break;

	  case '"':
	    if (yyres)
	      yyres[yyn] = '\0';
	    return yyn;
	  }
    do_not_strip_quotes: ;
    }

  if (! yyres)
    return yystrlen (yystr);

  return yystpcpy (yyres, yystr) - yyres;
}
# endif

/* Copy into *YYMSG, which is of size *YYMSG_ALLOC, an error message
   about the unexpected token YYTOKEN for the state stack whose top is
   YYSSP.

   Return 0 if *YYMSG was successfully written.  Return 1 if *YYMSG is
   not large enough to hold the message.  In that case, also set
   *YYMSG_ALLOC to the required number of bytes.  Return 2 if the
   required number of bytes is too large to store.  */
static int
yysyntax_error (YYSIZE_T *yymsg_alloc, char **yymsg,
                yytype_int16 *yyssp, int yytoken)
{
  YYSIZE_T yysize0 = yytnamerr (0, yytname[yytoken]);
  YYSIZE_T yysize = yysize0;
  YYSIZE_T yysize1;
  enum { YYERROR_VERBOSE_ARGS_MAXIMUM = 5 };
  /* Internationalized format string. */
  const char *yyformat = 0;
  /* Arguments of yyformat. */
  char const *yyarg[YYERROR_VERBOSE_ARGS_MAXIMUM];
  /* Number of reported tokens (one for the "unexpected", one per
     "expected"). */
  int yycount = 0;

  /* There are many possibilities here to consider:
     - Assume YYFAIL is not used.  It's too flawed to consider.  See
       <http://lists.gnu.org/archive/html/bison-patches/2009-12/msg00024.html>
       for details.  YYERROR is fine as it does not invoke this
       function.
     - If this state is a consistent state with a default action, then
       the only way this function was invoked is if the default action
       is an error action.  In that case, don't check for expected
       tokens because there are none.
     - The only way there can be no lookahead present (in yychar) is if
       this state is a consistent state with a default action.  Thus,
       detecting the absence of a lookahead is sufficient to determine
       that there is no unexpected or expected token to report.  In that
       case, just report a simple "syntax error".
     - Don't assume there isn't a lookahead just because this state is a
       consistent state with a default action.  There might have been a
       previous inconsistent state, consistent state with a non-default
       action, or user semantic action that manipulated yychar.
     - Of course, the expected token list depends on states to have
       correct lookahead information, and it depends on the parser not
       to perform extra reductions after fetching a lookahead from the
       scanner and before detecting a syntax error.  Thus, state merging
       (from LALR or IELR) and default reductions corrupt the expected
       token list.  However, the list is correct for canonical LR with
       one exception: it will still contain any token that will not be
       accepted due to an error action in a later state.
  */
  if (yytoken != YYEMPTY)
    {
      int yyn = yypact[*yyssp];
      yyarg[yycount++] = yytname[yytoken];
      if (!yypact_value_is_default (yyn))
        {
          /* Start YYX at -YYN if negative to avoid negative indexes in
             YYCHECK.  In other words, skip the first -YYN actions for
             this state because they are default actions.  */
          int yyxbegin = yyn < 0 ? -yyn : 0;
          /* Stay within bounds of both yycheck and yytname.  */
          int yychecklim = YYLAST - yyn + 1;
          int yyxend = yychecklim < YYNTOKENS ? yychecklim : YYNTOKENS;
          int yyx;

          for (yyx = yyxbegin; yyx < yyxend; ++yyx)
            if (yycheck[yyx + yyn] == yyx && yyx != YYTERROR
                && !yytable_value_is_error (yytable[yyx + yyn]))
              {
                if (yycount == YYERROR_VERBOSE_ARGS_MAXIMUM)
                  {
                    yycount = 1;
                    yysize = yysize0;
                    break;
                  }
                yyarg[yycount++] = yytname[yyx];
                yysize1 = yysize + yytnamerr (0, yytname[yyx]);
                if (! (yysize <= yysize1
                       && yysize1 <= YYSTACK_ALLOC_MAXIMUM))
                  return 2;
                yysize = yysize1;
              }
        }
    }

  switch (yycount)
    {
# define YYCASE_(N, S)                      \
      case N:                               \
        yyformat = S;                       \
      break
      YYCASE_(0, YY_("syntax error"));
      YYCASE_(1, YY_("syntax error, unexpected %s"));
      YYCASE_(2, YY_("syntax error, unexpected %s, expecting %s"));
      YYCASE_(3, YY_("syntax error, unexpected %s, expecting %s or %s"));
      YYCASE_(4, YY_("syntax error, unexpected %s, expecting %s or %s or %s"));
      YYCASE_(5, YY_("syntax error, unexpected %s, expecting %s or %s or %s or %s"));
# undef YYCASE_
    }

  yysize1 = yysize + yystrlen (yyformat);
  if (! (yysize <= yysize1 && yysize1 <= YYSTACK_ALLOC_MAXIMUM))
    return 2;
  yysize = yysize1;

  if (*yymsg_alloc < yysize)
    {
      *yymsg_alloc = 2 * yysize;
      if (! (yysize <= *yymsg_alloc
             && *yymsg_alloc <= YYSTACK_ALLOC_MAXIMUM))
        *yymsg_alloc = YYSTACK_ALLOC_MAXIMUM;
      return 1;
    }

  /* Avoid sprintf, as that infringes on the user's name space.
     Don't have undefined behavior even if the translation
     produced a string with the wrong number of "%s"s.  */
  {
    char *yyp = *yymsg;
    int yyi = 0;
    while ((*yyp = *yyformat) != '\0')
      if (*yyp == '%' && yyformat[1] == 's' && yyi < yycount)
        {
          yyp += yytnamerr (yyp, yyarg[yyi++]);
          yyformat += 2;
        }
      else
        {
          yyp++;
          yyformat++;
        }
  }
  return 0;
}
#endif /* YYERROR_VERBOSE */

/*-----------------------------------------------.
| Release the memory associated to this symbol.  |
`-----------------------------------------------*/

/*ARGSUSED*/
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
static void
yydestruct (const char *yymsg, int yytype, YYSTYPE *yyvaluep)
#else
static void
yydestruct (yymsg, yytype, yyvaluep)
    const char *yymsg;
    int yytype;
    YYSTYPE *yyvaluep;
#endif
{
  YYUSE (yyvaluep);

  if (!yymsg)
    yymsg = "Deleting";
  YY_SYMBOL_PRINT (yymsg, yytype, yyvaluep, yylocationp);

  switch (yytype)
    {

      default:
	break;
    }
}


/* Prevent warnings from -Wmissing-prototypes.  */
#ifdef YYPARSE_PARAM
#if defined __STDC__ || defined __cplusplus
int yyparse (void *YYPARSE_PARAM);
#else
int yyparse ();
#endif
#else /* ! YYPARSE_PARAM */
#if defined __STDC__ || defined __cplusplus
int yyparse (void);
#else
int yyparse ();
#endif
#endif /* ! YYPARSE_PARAM */


/*----------.
| yyparse.  |
`----------*/

#ifdef YYPARSE_PARAM
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
int
yyparse (void *YYPARSE_PARAM)
#else
int
yyparse (YYPARSE_PARAM)
    void *YYPARSE_PARAM;
#endif
#else /* ! YYPARSE_PARAM */
#if (defined __STDC__ || defined __C99__FUNC__ \
     || defined __cplusplus || defined _MSC_VER)
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

    int yystate;
    /* Number of tokens to shift before error messages enabled.  */
    int yyerrstatus;

    /* The stacks and their tools:
       `yyss': related to states.
       `yyvs': related to semantic values.

       Refer to the stacks thru separate pointers, to allow yyoverflow
       to reallocate them elsewhere.  */

    /* The state stack.  */
    yytype_int16 yyssa[YYINITDEPTH];
    yytype_int16 *yyss;
    yytype_int16 *yyssp;

    /* The semantic value stack.  */
    YYSTYPE yyvsa[YYINITDEPTH];
    YYSTYPE *yyvs;
    YYSTYPE *yyvsp;

    YYSIZE_T yystacksize;

  int yyn;
  int yyresult;
  /* Lookahead token as an internal (translated) token number.  */
  int yytoken;
  /* The variables used to return semantic value and location from the
     action routines.  */
  YYSTYPE yyval;

#if YYERROR_VERBOSE
  /* Buffer for error messages, and its allocated size.  */
  char yymsgbuf[128];
  char *yymsg = yymsgbuf;
  YYSIZE_T yymsg_alloc = sizeof yymsgbuf;
#endif

#define YYPOPSTACK(N)   (yyvsp -= (N), yyssp -= (N))

  /* The number of symbols on the RHS of the reduced rule.
     Keep to zero when no symbol should be popped.  */
  int yylen = 0;

  yytoken = 0;
  yyss = yyssa;
  yyvs = yyvsa;
  yystacksize = YYINITDEPTH;

  YYDPRINTF ((stderr, "Starting parse\n"));

  yystate = 0;
  yyerrstatus = 0;
  yynerrs = 0;
  yychar = YYEMPTY; /* Cause a token to be read.  */

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
     have just been pushed.  So pushing a state here evens the stacks.  */
  yyssp++;

 yysetstate:
  *yyssp = yystate;

  if (yyss + yystacksize - 1 <= yyssp)
    {
      /* Get the current used size of the three stacks, in elements.  */
      YYSIZE_T yysize = yyssp - yyss + 1;

#ifdef yyoverflow
      {
	/* Give user a chance to reallocate the stack.  Use copies of
	   these so that the &'s don't force the real ones into
	   memory.  */
	YYSTYPE *yyvs1 = yyvs;
	yytype_int16 *yyss1 = yyss;

	/* Each stack pointer address is followed by the size of the
	   data in use in that stack, in bytes.  This used to be a
	   conditional around just the two extra args, but that might
	   be undefined if yyoverflow is a macro.  */
	yyoverflow (YY_("memory exhausted"),
		    &yyss1, yysize * sizeof (*yyssp),
		    &yyvs1, yysize * sizeof (*yyvsp),
		    &yystacksize);

	yyss = yyss1;
	yyvs = yyvs1;
      }
#else /* no yyoverflow */
# ifndef YYSTACK_RELOCATE
      goto yyexhaustedlab;
# else
      /* Extend the stack our own way.  */
      if (YYMAXDEPTH <= yystacksize)
	goto yyexhaustedlab;
      yystacksize *= 2;
      if (YYMAXDEPTH < yystacksize)
	yystacksize = YYMAXDEPTH;

      {
	yytype_int16 *yyss1 = yyss;
	union yyalloc *yyptr =
	  (union yyalloc *) YYSTACK_ALLOC (YYSTACK_BYTES (yystacksize));
	if (! yyptr)
	  goto yyexhaustedlab;
	YYSTACK_RELOCATE (yyss_alloc, yyss);
	YYSTACK_RELOCATE (yyvs_alloc, yyvs);
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

  if (yystate == YYFINAL)
    YYACCEPT;

  goto yybackup;

/*-----------.
| yybackup.  |
`-----------*/
yybackup:

  /* Do appropriate processing given the current state.  Read a
     lookahead token if we need one and don't already have one.  */

  /* First try to decide what to do without reference to lookahead token.  */
  yyn = yypact[yystate];
  if (yypact_value_is_default (yyn))
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
      YY_SYMBOL_PRINT ("Next token is", yytoken, &yylval, &yylloc);
    }

  /* If the proper action on seeing token YYTOKEN is to reduce or to
     detect an error, take that action.  */
  yyn += yytoken;
  if (yyn < 0 || YYLAST < yyn || yycheck[yyn] != yytoken)
    goto yydefault;
  yyn = yytable[yyn];
  if (yyn <= 0)
    {
      if (yytable_value_is_error (yyn))
        goto yyerrlab;
      yyn = -yyn;
      goto yyreduce;
    }

  /* Count tokens shifted since error; after three, turn off error
     status.  */
  if (yyerrstatus)
    yyerrstatus--;

  /* Shift the lookahead token.  */
  YY_SYMBOL_PRINT ("Shifting", yytoken, &yylval, &yylloc);

  /* Discard the shifted token.  */
  yychar = YYEMPTY;

  yystate = yyn;
  *++yyvsp = yylval;

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

/* Line 1806 of yacc.c  */
#line 180 "htmlparse.y"
    {
    /* parse a single element */
}
    break;

  case 3:

/* Line 1806 of yacc.c  */
#line 183 "htmlparse.y"
    {
    /* parse a list of elements */
}
    break;

  case 4:

/* Line 1806 of yacc.c  */
#line 188 "htmlparse.y"
    {
    /* wait for more lexer input */
    YYACCEPT;
}
    break;

  case 5:

/* Line 1806 of yacc.c  */
#line 193 "htmlparse.y"
    {
    /* an error occured in the scanner, the python exception must be set */
    UserData* ud = yyget_extra(scanner);
    PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
    YYABORT;
}
    break;

  case 6:

/* Line 1806 of yacc.c  */
#line 200 "htmlparse.y"
    {
    /* parsed HTML start tag (eg. <a href="blubb">)
       $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a ListDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM((yyvsp[(1) - (1)]), 0);
    PyObject* attrs = PyTuple_GET_ITEM((yyvsp[(1) - (1)]), 1);
    int error = 0;
    int cmp;
    CHECK_ERROR((tag == NULL || attrs == NULL), finish_start);
    cmp = PyObject_RichCompareBool(tag, u_meta, Py_EQ);
    CHECK_ERROR((cmp == -1), finish_start);
    if (cmp == 1) {
        /* set encoding */
        result = PyObject_CallFunction(set_encoding, "OO", ud->parser, attrs);
        CHECK_ERROR((result == NULL), finish_start);
        Py_CLEAR(result);
    }
    if (PyObject_HasAttrString(ud->handler, "start_element") == 1) {
	callback = PyObject_GetAttrString(ud->handler, "start_element");
	CHECK_ERROR((!callback), finish_start);
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	CHECK_ERROR((!result), finish_start);
	Py_CLEAR(callback);
        Py_CLEAR(result);
    }
finish_start:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 7:

/* Line 1806 of yacc.c  */
#line 241 "htmlparse.y"
    {
    /* parsed HTML start-end tag (eg. <br/>)
       $1 is a PyTuple (<tag>, <attrs>)
       <tag> is a PyObject, <attrs> is a ListDict */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    PyObject* tag = PyTuple_GET_ITEM((yyvsp[(1) - (1)]), 0);
    PyObject* attrs = PyTuple_GET_ITEM((yyvsp[(1) - (1)]), 1);
    int error = 0;
    int cmp;
    char* fname;
    PyObject* tagname;
    CHECK_ERROR((tag == NULL || attrs == NULL), finish_start_end);
    tagname = PyUnicode_AsEncodedString(tag, "ascii", "ignore");
    CHECK_ERROR((tagname == NULL), finish_start_end);
    cmp = PyObject_RichCompareBool(tag, u_meta, Py_EQ);
    CHECK_ERROR((cmp == -1), finish_start_end);
    if (cmp == 1) {
        /* set encoding */
        result = PyObject_CallFunction(set_encoding, "OO", ud->parser, attrs);
        CHECK_ERROR((result == NULL), finish_start_end);
        Py_CLEAR(result);
    }
    cmp = html_end_tag(tagname, ud->parser);
    CHECK_ERROR((cmp < 0), finish_start_end);
    fname = (cmp == 0 ? "start_element" : "start_end_element");
    if (PyObject_HasAttrString(ud->handler, fname) == 1) {
	callback = PyObject_GetAttrString(ud->handler, fname);
	CHECK_ERROR((!callback), finish_start_end);
	result = PyObject_CallFunction(callback, "OO", tag, attrs);
	CHECK_ERROR((!result), finish_start_end);
	Py_CLEAR(callback);
        Py_CLEAR(result);
    }
finish_start_end:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_XDECREF(tag);
    Py_XDECREF(attrs);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 8:

/* Line 1806 of yacc.c  */
#line 289 "htmlparse.y"
    {
    /* parsed HTML end tag (eg. </b>)
       $1 is a PyUnicode with the tag name */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    int cmp;
    /* encode tagname in ASCII, ignoring any unknown chars */
    PyObject* tagname = PyUnicode_AsEncodedString((yyvsp[(1) - (1)]), "ascii", "ignore");
    if (tagname == NULL) {
        error = 1;
        goto finish_end;
    }
    cmp = html_end_tag(tagname, ud->parser);
    CHECK_ERROR((cmp < 0), finish_end);
    if (PyObject_HasAttrString(ud->handler, "end_element") == 1 && cmp > 0) {
	callback = PyObject_GetAttrString(ud->handler, "end_element");
	CHECK_ERROR((callback == NULL), finish_end);
	result = PyObject_CallFunction(callback, "O", (yyvsp[(1) - (1)]));
	CHECK_ERROR((result == NULL), finish_end);
	Py_CLEAR(callback);
	Py_CLEAR(result);
    }
finish_end:
    Py_XDECREF(tagname);
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 9:

/* Line 1806 of yacc.c  */
#line 325 "htmlparse.y"
    {
    /* parsed HTML comment (eg. <!-- bla -->)
       $1 is a PyUnicode with the comment content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "comment", "O", (yyvsp[(1) - (1)]), finish_comment);
finish_comment:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 10:

/* Line 1806 of yacc.c  */
#line 344 "htmlparse.y"
    {
    /* $1 is a PyUnicode */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "pi", "O", (yyvsp[(1) - (1)]), finish_pi);
finish_pi:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 11:

/* Line 1806 of yacc.c  */
#line 362 "htmlparse.y"
    {
    /* parsed HTML CDATA (eg. <![CDATA[spam and eggs ...]]>)
       $1 is a PyUnicode with the CDATA content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "cdata", "O", (yyvsp[(1) - (1)]), finish_cdata);
finish_cdata:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 12:

/* Line 1806 of yacc.c  */
#line 381 "htmlparse.y"
    {
    /* parsed HTML doctype (eg. <!DOCTYPE imadoofus system>)
       $1 is a PyUnicode with the doctype content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    /* set encoding */
    result = PyObject_CallFunction(set_doctype, "OO", ud->parser, (yyvsp[(1) - (1)]));
    CHECK_ERROR((result == NULL), finish_doctype);
    Py_CLEAR(result);
    CALLBACK(ud, "doctype", "O", (yyvsp[(1) - (1)]), finish_doctype);
finish_doctype:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 13:

/* Line 1806 of yacc.c  */
#line 404 "htmlparse.y"
    {
    /* parsed HTML script content (plus end tag which is omitted)
       $1 is a PyUnicode with the script content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* script = PyUnicode_DecodeASCII("script", 6, "ignore");
    CHECK_ERROR((script == NULL), finish_script);
    CALLBACK(ud, "characters", "O", (yyvsp[(1) - (1)]), finish_script);
    /* emit the omitted end tag */
    CALLBACK(ud, "end_element", "O", script, finish_script);
finish_script:
    Py_XDECREF(callback);
    Py_XDECREF(script);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 14:

/* Line 1806 of yacc.c  */
#line 428 "htmlparse.y"
    {
    /* parsed HTML style content (plus end tag which is omitted)
       $1 is a PyUnicode with the style content */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    PyObject* style = PyUnicode_DecodeASCII("style", 5, "ignore");
    CHECK_ERROR((style == NULL), finish_style);
    CALLBACK(ud, "characters", "O", (yyvsp[(1) - (1)]), finish_style);
    /* emit the omitted end tag */
    CALLBACK(ud, "end_element", "O", style, finish_style);
finish_style:
    Py_XDECREF(callback);
    Py_XDECREF(style);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;

  case 15:

/* Line 1806 of yacc.c  */
#line 452 "htmlparse.y"
    {
    /* parsed HTML text data
       $1 is a PyUnicode with the text */
    /* Remember this is also called as a lexer fallback when no
       HTML structure element could be recognized. */
    UserData* ud = yyget_extra(scanner);
    PyObject* callback = NULL;
    PyObject* result = NULL;
    int error = 0;
    CALLBACK(ud, "characters", "O", (yyvsp[(1) - (1)]), finish_characters);
finish_characters:
    Py_XDECREF(callback);
    Py_XDECREF(result);
    Py_DECREF((yyvsp[(1) - (1)]));
    if (error) {
	PyErr_Fetch(&(ud->exc_type), &(ud->exc_val), &(ud->exc_tb));
	YYABORT;
    }
    SET_OLD_LINECOL;
}
    break;



/* Line 1806 of yacc.c  */
#line 1872 "htmlparse.c"
      default: break;
    }
  /* User semantic actions sometimes alter yychar, and that requires
     that yytoken be updated with the new translation.  We take the
     approach of translating immediately before every use of yytoken.
     One alternative is translating here after every semantic action,
     but that translation would be missed if the semantic action invokes
     YYABORT, YYACCEPT, or YYERROR immediately after altering yychar or
     if it invokes YYBACKUP.  In the case of YYABORT or YYACCEPT, an
     incorrect destructor might then be invoked immediately.  In the
     case of YYERROR or YYBACKUP, subsequent parser actions might lead
     to an incorrect destructor call or verbose syntax error message
     before the lookahead is translated.  */
  YY_SYMBOL_PRINT ("-> $$ =", yyr1[yyn], &yyval, &yyloc);

  YYPOPSTACK (yylen);
  yylen = 0;
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
  /* Make sure we have latest lookahead translation.  See comments at
     user semantic actions for why this is necessary.  */
  yytoken = yychar == YYEMPTY ? YYEMPTY : YYTRANSLATE (yychar);

  /* If not already recovering from an error, report this error.  */
  if (!yyerrstatus)
    {
      ++yynerrs;
#if ! YYERROR_VERBOSE
      yyerror (YY_("syntax error"));
#else
# define YYSYNTAX_ERROR yysyntax_error (&yymsg_alloc, &yymsg, \
                                        yyssp, yytoken)
      {
        char const *yymsgp = YY_("syntax error");
        int yysyntax_error_status;
        yysyntax_error_status = YYSYNTAX_ERROR;
        if (yysyntax_error_status == 0)
          yymsgp = yymsg;
        else if (yysyntax_error_status == 1)
          {
            if (yymsg != yymsgbuf)
              YYSTACK_FREE (yymsg);
            yymsg = (char *) YYSTACK_ALLOC (yymsg_alloc);
            if (!yymsg)
              {
                yymsg = yymsgbuf;
                yymsg_alloc = sizeof yymsgbuf;
                yysyntax_error_status = 2;
              }
            else
              {
                yysyntax_error_status = YYSYNTAX_ERROR;
                yymsgp = yymsg;
              }
          }
        yyerror (yymsgp);
        if (yysyntax_error_status == 2)
          goto yyexhaustedlab;
      }
# undef YYSYNTAX_ERROR
#endif
    }



  if (yyerrstatus == 3)
    {
      /* If just tried and failed to reuse lookahead token after an
	 error, discard it.  */

      if (yychar <= YYEOF)
	{
	  /* Return failure if at end of input.  */
	  if (yychar == YYEOF)
	    YYABORT;
	}
      else
	{
	  yydestruct ("Error: discarding",
		      yytoken, &yylval);
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

  /* Pacify compilers like GCC when the user code never invokes
     YYERROR and the label yyerrorlab therefore never appears in user
     code.  */
  if (/*CONSTCOND*/ 0)
     goto yyerrorlab;

  /* Do not reclaim the symbols of the rule which action triggered
     this YYERROR.  */
  YYPOPSTACK (yylen);
  yylen = 0;
  YY_STACK_PRINT (yyss, yyssp);
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
      if (!yypact_value_is_default (yyn))
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


      yydestruct ("Error: popping",
		  yystos[yystate], yyvsp);
      YYPOPSTACK (1);
      yystate = *yyssp;
      YY_STACK_PRINT (yyss, yyssp);
    }

  *++yyvsp = yylval;


  /* Shift the error token.  */
  YY_SYMBOL_PRINT ("Shifting", yystos[yyn], yyvsp, yylsp);

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

#if !defined(yyoverflow) || YYERROR_VERBOSE
/*-------------------------------------------------.
| yyexhaustedlab -- memory exhaustion comes here.  |
`-------------------------------------------------*/
yyexhaustedlab:
  yyerror (YY_("memory exhausted"));
  yyresult = 2;
  /* Fall through.  */
#endif

yyreturn:
  if (yychar != YYEMPTY)
    {
      /* Make sure we have latest lookahead translation.  See comments at
         user semantic actions for why this is necessary.  */
      yytoken = YYTRANSLATE (yychar);
      yydestruct ("Cleanup: discarding lookahead",
                  yytoken, &yylval);
    }
  /* Do not reclaim the symbols of the rule which action triggered
     this YYABORT or YYACCEPT.  */
  YYPOPSTACK (yylen);
  YY_STACK_PRINT (yyss, yyssp);
  while (yyssp != yyss)
    {
      yydestruct ("Cleanup: popping",
		  yystos[*yyssp], yyvsp);
      YYPOPSTACK (1);
    }
#ifndef yyoverflow
  if (yyss != yyssa)
    YYSTACK_FREE (yyss);
#endif
#if YYERROR_VERBOSE
  if (yymsg != yymsgbuf)
    YYSTACK_FREE (yymsg);
#endif
  /* Make sure YYID is used.  */
  return YYID (yyresult);
}



/* Line 2067 of yacc.c  */
#line 474 "htmlparse.y"


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
    if (handler == NULL) {
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
    Py_VISIT(self->handler);
    return 0;
}


/* clear all used subobjects participating in reference cycles */
static int parser_clear (parser_object* self) {
    self->userData->handler = NULL;
    Py_CLEAR(self->handler);
    return 0;
}


/* free all allocated resources of parser object */
static void parser_dealloc (parser_object* self) {
    htmllexDestroy(self->scanner);
    parser_clear(self);
    self->userData->parser = NULL;
    Py_CLEAR(self->encoding);
    Py_CLEAR(self->doctype);
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
    Py_CLEAR(self->userData->tmp_tag);
    Py_CLEAR(self->userData->tmp_attrs);
    Py_CLEAR(self->userData->tmp_attrval);
    Py_CLEAR(self->userData->tmp_attrname);
    self->userData->bufpos = 0;
    if (strlen(self->userData->buf)) {
        int error = 0;
        int i;
       	PyObject* callback = NULL;
        PyObject* result = NULL;
        const char* enc;
        PyObject* s;
        /* set line, col */
        for (i=0; i<strlen(self->userData->buf); ++i) {
            if (self->userData->buf[i] == '\n') {
                ++(self->userData->lineno);
                self->userData->column = 1;
            }
            else ++(self->userData->column);
        }
        enc = PyString_AsString(self->encoding);
        s = PyUnicode_Decode(self->userData->buf,
               (Py_ssize_t)strlen(self->userData->buf), enc, "ignore");
        /* reset buffer */
        CLEAR_BUF(self->userData->buf);
        if (s == NULL) { error = 1; goto finish_flush; }
        if (PyObject_HasAttrString(self->handler, "characters") == 1) {
            callback = PyObject_GetAttrString(self->handler, "characters");
            if (callback == NULL) { error = 1; goto finish_flush; }
            result = PyObject_CallFunction(callback, "O", s);
            if (result == NULL) { error = 1; goto finish_flush; }
        }
    finish_flush:
	Py_XDECREF(callback);
	Py_XDECREF(result);
	Py_XDECREF(s);
	if (error == 1) {
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


/* return buffered parser data up to given length */
static PyObject* parser_peek (parser_object* self, PyObject* args) {
    Py_ssize_t len, buflen;
    if (!PyArg_ParseTuple(args, "n", &len)) {
        return NULL;
    }
    if (len < 0) {
	PyErr_SetString(PyExc_TypeError, "peek length must not be negative");
        return NULL;
    }
    buflen = strlen(self->userData->buf);
    if (!buflen || self->userData->bufpos >= buflen) {
        return PyString_FromString("");
    }
    if (self->userData->bufpos + len >= buflen) {
        len = buflen - self->userData->bufpos - 1;
    }
    return PyString_FromStringAndSize(self->userData->buf + self->userData->bufpos, len);
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


/* get SAX handler object */
static PyObject* parser_gethandler (parser_object* self, void* closure) {
    Py_INCREF(self->handler);
    return self->handler;
}


/* set SAX handler object */
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


/* get parser encoding */
static PyObject* parser_getencoding (parser_object* self, void* closure) {
    Py_INCREF(self->encoding);
    return self->encoding;
}


/* set parser encoding */
static int parser_setencoding (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete encoding");
        return -1;
    }
    if (!PyString_CheckExact(value)) {
        PyErr_SetString(PyExc_TypeError, "encoding must be string");
        return -1;
    }
    Py_DECREF(self->encoding);
    Py_INCREF(value);
    self->encoding = value;
    if (yydebug > 0) {
        /* print debug message */
        PyObject* repr = PyObject_Repr(value);
        if (repr == NULL) {
            return -1;
        }
        fprintf(stderr, "htmlsax: set encoding to %s\n", PyString_AsString(repr));
        Py_DECREF(repr);
    }
    return 0;
}


/* get parser doctype */
static PyObject* parser_getdoctype (parser_object* self, void* closure) {
    Py_INCREF(self->doctype);
    return self->doctype;
}


/* set parser doctype */
static int parser_setdoctype (parser_object* self, PyObject* value, void* closure) {
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete doctype");
        return -1;
    }
    if (!PyString_CheckExact(value)) {
        PyObject* repr = PyObject_Repr(value);
        char* cp = PyString_AsString(repr);
        if (NULL == cp)
            return -1;
        PyErr_Format(PyExc_TypeError, "doctype %s must be string", cp);
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
    {"peek", (PyCFunction)parser_peek, METH_VARARGS, "get up to given length of buffered data from current parse position"},
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
    if ((m = Py_InitModule3("htmlsax", htmlsax_methods, "SAX HTML parser routines")) == NULL) {
        return;
    }
    Py_INCREF(&parser_type);
    if (PyModule_AddObject(m, "parser", (PyObject*)&parser_type) == -1) {
        /* init error */
        PyErr_Print();
    }
    if ((m = PyImport_ImportModule("linkcheck.HtmlParser")) == NULL) {
        return;
    }
    if ((resolve_entities = PyObject_GetAttrString(m, "resolve_entities")) == NULL) {
        Py_DECREF(m);
        return;
    }
    if ((set_encoding = PyObject_GetAttrString(m, "set_encoding")) == NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(m);
        return;
    }
    if ((set_doctype = PyObject_GetAttrString(m, "set_doctype")) == NULL) {
        Py_DECREF(resolve_entities);
        Py_DECREF(set_encoding);
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
    if ((u_meta = PyString_Decode("meta", 4, "ascii", "ignore")) == NULL) {
        return;
    }
    if ((m = PyImport_ImportModule("linkcheck.containers")) == NULL) {
        return;
    }
    if ((list_dict = PyObject_GetAttrString(m, "ListDict")) == NULL) {
        Py_DECREF(m);
        return;
    }
    Py_DECREF(m);
}

