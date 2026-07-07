#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

char message[] = "Welcome!";

unsigned char xor_key;

__attribute__((constructor)) void seed_random() {
    srand(time(NULL));
    xor_key = 0x60 + (rand() % (0xc0 - 0x60 + 1));
}

char* enc(const char* input, char key, int len){
    char* buffer = malloc(128);
    for(int i = 0; i < len; i++){
        buffer[i] = input[i] ^ key;
    }
    return buffer;
}

void chall(){
    printf("Here is your unique XOR key: 0x%x\n", xor_key);
    char password[16];
    char username[128];
    char email[0x100];
    printf("Enter your username: ");
    int num_bytes = read(0, username, 128);
    char* result = enc(username, xor_key, num_bytes);
    printf("Here is your encrypted username: ");
    printf(result);
    printf("\n");
    printf("Enter your email: ");
    num_bytes = read(0, email, 128);
    result = enc(email, xor_key, num_bytes);
    printf("Here is your encrypted email: ");
    printf(result);
    printf("\n");
    printf("Enter your password: ");
    num_bytes = read(0, password, 16);
    puts(message);
}

int main() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    chall();
    return 0;
}