#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>

void win(void *start, void *end)
{
    uintptr_t s = (uintptr_t)start;
    uintptr_t e = (uintptr_t)end;

    /* Align to page boundaries */
    s &= ~0xfffUL;
    e = (e + 0xfffUL) & ~0xfffUL;

    if (e <= s)
    {
        puts("bad range");
        exit(1);
    }

    if (e - s > 0x2000)
    {
        puts("range too large");
        exit(1);
    }

    if (mprotect((void *)s,
                 e - s,
                 PROT_READ | PROT_WRITE | PROT_EXEC) != 0)
    {
        perror("mprotect");
        exit(1);
    }

    puts("Here's your price");
}

void vuln(void)
{
    char buf[128];

    printf("buf = %p\n", buf);

    puts("show me what you've got");

    gets(buf);
}

int main(void)
{
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);

    vuln();

    puts("bye");

    return 0;
}