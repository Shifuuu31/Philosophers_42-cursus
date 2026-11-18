#!/usr/bin/env python3
import subprocess
import time
import re
import sys
import os
import shutil

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS = f"{GREEN}{BOLD}[PASS]{RESET}"
FAIL = f"{RED}{BOLD}[FAIL]{RESET}"

PHILO_BIN = os.path.abspath("./philo")
passed_count = 0
failed_count = 0

def kill_philo():
    subprocess.run(["pkill", "-9", "philo"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "philo_tsan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_timestamps(lines):
    prev_ts = -1
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0].isdigit():
            ts = int(parts[0])
            if prev_ts != -1 and ts < prev_ts:
                return False, f"Timestamp out of order: {ts} after {prev_ts}"
            prev_ts = ts
    return True, ""

def run_test(name, args, expected_death=None, min_death_ts=None, max_death_ts=None, 
             should_error=False, timeout=10, binary=PHILO_BIN):
    global passed_count, failed_count
    kill_philo()
    
    cmd = [binary] + [str(a) for a in args]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, timeout=timeout)
        duration = time.time() - t0
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as e:
        kill_philo()
        print(f" {FAIL} {name} (Timed out after {timeout}s)")
        failed_count += 1
        return False

    lines = [l for l in stdout.splitlines() if l.strip()]
    
    # 1. Error handling test
    if should_error:
        if proc.returncode != 0 or any("error" in l.lower() for l in lines) or any("error" in l.lower() for l in stderr.splitlines()):
            print(f" {PASS} {name} (Error detected gracefully)")
            passed_count += 1
            return True
        else:
            print(f" {FAIL} {name} (Expected error, but program executed normally)")
            failed_count += 1
            return False

    # 2. Timestamp ordering
    ts_ok, ts_msg = check_timestamps(lines)
    if not ts_ok:
        print(f" {FAIL} {name} ({ts_msg})")
        failed_count += 1
        return False

    # 3. Death check
    death_lines = [l for l in lines if "died" in l]
    if expected_death is True:
        if not death_lines:
            print(f" {FAIL} {name} (Expected death, but no philosopher died)")
            failed_count += 1
            return False
        # Check death delay precision
        death_ts = int(death_lines[0].split()[0])
        if min_death_ts is not None and death_ts < min_death_ts:
            print(f" {FAIL} {name} (Philosopher died too early: {death_ts}ms < {min_death_ts}ms)")
            failed_count += 1
            return False
        if max_death_ts is not None and death_ts > max_death_ts:
            print(f" {FAIL} {name} (Philosopher died too late: {death_ts}ms > {max_death_ts}ms, delay={death_ts - min_death_ts}ms)")
            failed_count += 1
            return False
    elif expected_death is False:
        if death_lines:
            death_ts = death_lines[0].split()[0]
            print(f" {FAIL} {name} (Unexpected death at {death_ts}ms: '{death_lines[0]}')")
            failed_count += 1
            return False

    print(f" {PASS} {name} ({duration:.2f}s)")
    passed_count += 1
    return True

def run_tsan_check():
    global passed_count, failed_count
    print(f"\n{CYAN}{BOLD}[6. ThreadSanitizer Concurrency & Data Race Check]{RESET}")
    tsan_bin = "./philo_tsan"
    compile_cmd = [
        "cc", "-Wall", "-Wextra", "-Werror", "-pthread", "-fsanitize=thread", "-g", "-Iinclude",
        "src/main.c", "src/parsing.c", "src/monitor.c", "src/routine.c", "src/utils.c", "-o", tsan_bin
    ]
    res = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f" {FAIL} TSan Compilation failed: {res.stderr}")
        failed_count += 1
        return

    # Run TSan on 4 philos with 3 meals
    proc = subprocess.run([tsan_bin, "4", "410", "200", "200", "3"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
    if "ThreadSanitizer: data race" in proc.stderr:
        print(f" {FAIL} TSan detected data race in '4 410 200 200 3'!")
        print(proc.stderr[:400])
        failed_count += 1
    else:
        print(f" {PASS} TSan clean on 4 philosophers (no data race)")
        passed_count += 1

    # Run TSan on death case
    proc = subprocess.run([tsan_bin, "1", "300", "200", "200"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
    if "ThreadSanitizer: data race" in proc.stderr:
        print(f" {FAIL} TSan detected data race in single philosopher death!")
        failed_count += 1
    else:
        print(f" {PASS} TSan clean on death scenario (no data race)")
        passed_count += 1

    if os.path.exists(tsan_bin):
        os.remove(tsan_bin)

def main():
    if not os.path.isfile(PHILO_BIN):
        print(f"{RED}Error: {PHILO_BIN} not found. Run 'make' first.{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{CYAN}       42 PHILOSOPHERS - HARD TEST SUITE              {RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}\n")

    # 1. Input parsing
    print(f"{CYAN}{BOLD}[1. Argument & Edge Parsing Checks]{RESET}")
    run_test("No arguments", [], should_error=True)
    run_test("Negative philosopher count", ["-5", "800", "200", "200"], should_error=True)
    run_test("Zero philosophers", ["0", "800", "200", "200"], should_error=True)
    run_test("Negative time to die", ["4", "-800", "200", "200"], should_error=True)
    run_test("Zero time to eat", ["4", "800", "0", "200"], should_error=True)
    run_test("Negative meals", ["4", "800", "200", "200", "-1"], should_error=True)
    run_test("Zero meals", ["4", "800", "200", "200", "0"], should_error=True)
    run_test("Non-numeric argument", ["4", "800", "200", "abc"], should_error=True)
    run_test("Too many arguments", ["4", "800", "200", "200", "5", "6"], should_error=True)

    # 2. Single Philosopher
    print(f"\n{CYAN}{BOLD}[2. Single Philosopher (Deadlock & Death Test)]{RESET}")
    run_test("Single philo (1 800 200 200)", ["1", "800", "200", "200"], 
             expected_death=True, min_death_ts=800, max_death_ts=815, timeout=3)
    run_test("Single philo fast (1 300 100 100)", ["1", "300", "100", "100"], 
             expected_death=True, min_death_ts=300, max_death_ts=315, timeout=2)

    # 3. Death Timing Precision (<15ms delay allowed)
    print(f"\n{CYAN}{BOLD}[3. Death Timing Precision Tests]{RESET}")
    run_test("Tight death timing (4 310 200 100)", ["4", "310", "200", "100"],
             expected_death=True, min_death_ts=310, max_death_ts=325, timeout=3)
    run_test("Immediate starvation (2 100 150 150)", ["2", "100", "150", "150"],
             expected_death=True, min_death_ts=100, max_death_ts=115, timeout=2)

    # 4. Meal Completion (No Death)
    print(f"\n{CYAN}{BOLD}[4. Meal Limit & Clean Termination Tests]{RESET}")
    run_test("4 philos, 3 meals (4 410 200 200 3)", ["4", "410", "200", "200", "3"],
             expected_death=False, timeout=5)
    run_test("5 philos, 5 meals (5 800 200 200 5)", ["5", "800", "200", "200", "5"],
             expected_death=False, timeout=8)
    run_test("2 philos, 4 meals (2 800 200 200 4)", ["2", "800", "200", "200", "4"],
             expected_death=False, timeout=6)

    # 5. High Load Concurrency Stress Tests
    print(f"\n{CYAN}{BOLD}[5. Concurrency Stress Tests (High Thread Counts)]{RESET}")
    run_test("50 philos (50 800 100 100 3)", ["50", "800", "100", "100", "3"],
             expected_death=False, timeout=10)
    run_test("100 philos (100 800 100 100 2)", ["100", "800", "100", "100", "2"],
             expected_death=False, timeout=12)
    run_test("198 philos (198 800 100 100 2)", ["198", "800", "100", "100", "2"],
             expected_death=False, timeout=15)

    # 6. ThreadSanitizer
    run_tsan_check()

    kill_philo()

    # Final summary
    total = passed_count + failed_count
    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    if failed_count == 0:
        print(f"{BOLD}{GREEN}ALL {total} HARD TESTS PASSED SUCCESSFULLY! {RESET}")
    else:
        print(f"{BOLD}{RED}FAILED {failed_count} OF {total} TESTS.{RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}\n")

    sys.exit(0 if failed_count == 0 else 1)

if __name__ == "__main__":
    main()
