#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

struct profile {
	char name[0x20];
	FILE *stream;
};

struct profile profile = {
	.name = "guest",
};

static void read_exact(void *buf, size_t size)
{
	size_t done = 0;

	while (done < size) {
		ssize_t n = read(STDIN_FILENO, (char *)buf + done, size - done);
		if (n <= 0)
			exit(0);
		done += (size_t)n;
	}
}

static unsigned long read_ulong(void)
{
	char buf[0x20] = {0};
	size_t i = 0;

	while (i + 1 < sizeof(buf)) {
		ssize_t n = read(STDIN_FILENO, &buf[i], 1);
		if (n <= 0)
			exit(0);
		if (buf[i++] == '\n')
			break;
	}

	return strtoul(buf, NULL, 0);
}

int main(void)
{
	long *large;
	char *title = NULL;

	setbuf(stdin, NULL);
	setbuf(stdout, NULL);
	setbuf(stderr, NULL);

	profile.stream = stdout;
	large = malloc(0x420);

	for (;;) {
		puts("1. new title");
		puts("2. update");
		puts("3. rename");
		puts("4. show");
		puts("5. delete title");
		puts("6. exit");
		printf("> ");

		switch (read_ulong()) {
		case 1:
			if (title) {
				puts("no");
				break;
			}
			title = malloc(0x10);
			printf("title: ");
			read_exact(title, 0x10);
			puts("ok");
			break;
		case 2:
			printf("data: ");
			read_exact(large, 0x4d0);
			puts("ok");
			break;
		case 3:
			printf("name: ");
			read_exact(profile.name, sizeof(profile.name));
			puts("ok");
			break;
		case 4:
			printf("name: %s\n", profile.name);
			break;
		case 5:
			if (!title) {
				puts("no");
				break;
			}
			free(title);
			title = NULL;
			puts("ok");
			break;
		case 6:
			return 0;
		default:
			puts("?");
			break;
		}
	}
}
