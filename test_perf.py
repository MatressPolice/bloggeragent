import time
import os

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(AGENT_DIR, "frontend")
FRONTEND_DIR_ABSPATH_PREFIX = os.path.abspath(FRONTEND_DIR) + os.path.sep

def benchmark_direct(iterations=100000):
    start = time.time()
    for i in range(iterations):
        norm_path = f"/static/file{i}.js"
        file_path = os.path.join(FRONTEND_DIR, norm_path.lstrip("/"))
        # current code equivalent
        is_static = os.path.abspath(file_path).startswith(os.path.abspath(FRONTEND_DIR) + os.path.sep)
    end = time.time()
    baseline = end - start
    print(f"Current code (re-calculating abspath): {baseline:.4f} seconds")

    start = time.time()
    for i in range(iterations):
        norm_path = f"/static/file{i}.js"
        file_path = os.path.join(FRONTEND_DIR, norm_path.lstrip("/"))
        # optimized code equivalent
        is_static = os.path.abspath(file_path).startswith(FRONTEND_DIR_ABSPATH_PREFIX)
    end = time.time()
    optimized = end - start
    print(f"Optimized code (using cached abspath prefix): {optimized:.4f} seconds")
    print(f"Improvement: {(baseline - optimized) / baseline * 100:.2f}%")

if __name__ == '__main__':
    benchmark_direct()
