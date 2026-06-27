def main():
    questions = [
        { 
            "question": "Apa nama dan PID dari process yang mencurigakan? (case sensitive)",
            "format": "nama:pid",
            "case_sensitive": True
        },
        { 
            "question": "Apa nama dan PID dari executable yang memulai proses mencurigakan? (case sensitive)",
            "format": "nama:pid",
            "case_sensitive": True
        },
        { 
            "question": "Apa sha256 hash dari executable",
            "format": "-",
            "case_sensitive": True
        },
        {
            "question": "Apa algoritma enkripsi yang digunakan oleh executable? (case insensitive)",
            "format": "-",
            "case_sensitive": False
        },
        { 
            "question": "Apa cara rahasia agar bisa masuk netsos? (case insensitive)",
            "format": "-",
            "case_sensitive": False
        },
    ]

    answers = [
        "Encryptor:1969",
        "netsos:1968",
        "459c3031178c91af4456f3c6e42c80fa843cd91d0a74ff46666a00d2c06f7535",
        ["aes256cbc", "aes-256-cbc", "aes 256 cbc", "aes_256_cbc"],
        "rajin ikut ceteep dan belajar",
    ]

    print("Silahkan jawab pertanyaan-pertanyaan yang telah disediakan:")

    correct_answers = 0

    for index, q in enumerate(questions, start=1):
        print(f"\nNo {index}:")
        print("Pertanyaan: " + q["question"])
        print("Format: " + q["format"])
        user_answer = input("Jawaban: ").strip()

        expected = answers[index - 1]

        if isinstance(expected, list):
            if any(
                user_answer.lower() == opt.lower() if not q["case_sensitive"] else user_answer == opt
                for opt in expected
            ):
                print("Correct")
                correct_answers += 1
            else:
                print("Incorrect")
                return
        else:
            if q["case_sensitive"]:
                if user_answer == expected:
                    print("Correct")
                    correct_answers += 1
                else:
                    print("Incorrect")
                    return
            else:
                if user_answer.lower() == expected.lower():
                    print("Correct")
                    correct_answers += 1
                else:
                    print("Incorrect")
                    return

    if correct_answers == len(questions):
        print("\nCongrats! Flag: NETSOS{intro_to_vol4tility_4nd_mem_analysis_gampan9_lah_ya_seman9at_ngerjain_soal-soal_lain_semoga_juara}")

if __name__ == "__main__":
    main()
