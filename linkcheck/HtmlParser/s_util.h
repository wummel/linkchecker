/*
 *  linux/lib/string.c
 *
 *  Copyright (C) 1991, 1992  Linus Torvalds
 */
#include <string.h>

#if !defined(HAVE_STRLCPY)
size_t strlcpy(char *dst, const char *src, size_t size);
#endif /* !HAVE_STRLCPY */

#if !defined(HAVE_STRLCAT)
size_t strlcat(char *dst, const char *src, size_t size);
#endif /* !HAVE_STRLCAT */
