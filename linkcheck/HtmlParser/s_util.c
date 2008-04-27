/*
 *  linux/lib/string.c
 *
 *  Copyright (C) 1991, 1992  Linus Torvalds
 */
#include "Python.h"

#if !defined(HAVE_STRLCPY)
/**
 * strlcpy - Copy a %NUL terminated string into a sized buffer
 * @dst: Where to copy the string to
 * @src: Where to copy the string from
 * @size: size of destination buffer
 *
 * Compatible with *BSD: the result is always a valid
 * NUL-terminated string that fits in the buffer (unless,
 * of course, the buffer size is zero). It does not pad
 * out the result like strncpy() does.
 */
size_t strlcpy (char *dst, const char *src, size_t size)
{
    size_t ret = strlen(src);
    if (size > 0) {
        size_t len = (ret >= size) ? size-1 : ret;
        Py_MEMCPY(dst, src, len);
        dst[len] = '\0';
    }
    return ret;
}
#endif /* !HAVE_STRLCPY */

#if !defined(HAVE_STRLCAT)
/**
 * strlcat - Append a length-limited, %NUL-terminated string to another
 * @dst: The string to be appended to
 * @src: The string to append to it
 * @size: The size of the destination buffer.
 */
size_t strlcat (char *dst, const char *src, size_t size)
{
    size_t dsize = strlen(dst);
    size_t len = strlen(src);
    size_t res = dsize + len;
    dst += dsize;
    size -= dsize;
    if (len >= size)
        len = size-1;
    Py_MEMCPY(dst, src, len);
    dst[len] = '\0';
    return res;
}
#endif /* !HAVE_STRLCAT */
