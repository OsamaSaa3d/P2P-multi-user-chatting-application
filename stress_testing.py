# sequential execution of peer.py

# import time, os, matplotlib.pyplot as plt

# times = []
# for i in range(100):
#     start_time = time.time()
#     os.system("python peer.py")
#     end_time = time.time()
#     execution_time = end_time - start_time
#     times.append(execution_time)
#     print(f"peer.py execution time: {execution_time} seconds")
#     print(f"Execution number: {i+1}")

# plt.plot(times)
# plt.ylabel('Execution time (seconds)')
# plt.xlabel('Execution number')
# plt.show()


# Parallel execution of peer.py
# import concurrent.futures
# import os
# import time
# import matplotlib.pyplot as plt

# def run_peer(i):
#     start_time = time.time()
#     os.system("python peer.py")
#     end_time = time.time()
#     execution_time = end_time - start_time
#     times.append(execution_time)
#     print(f"peer.py execution time for thread {i+1}: {execution_time} seconds")

# times = []
# num_executions = 1000

# with concurrent.futures.ThreadPoolExecutor() as executor:
#     futures = [executor.submit(run_peer, i) for i in range(num_executions)]

#     # Wait for all threads to complete
#     concurrent.futures.wait(futures)

# # Print the average execution time
# avg_execution_time = sum(times) / num_executions
# print(f"Average peer.py execution time: {avg_execution_time} seconds")

# plt.plot(times)
# plt.ylabel('Execution time (seconds)')
# plt.xlabel('Execution number')
# plt.show()


# Parallel execution of peer.py but there are 100 users already connected to the system

import concurrent.futures
import os
import time
import matplotlib.pyplot as plt
import subprocess

def run_peer_permenant():
    command = r'start cmd /k python "C:\Users\Osama\Desktop\finalfinal\P2P-multi-user-chatting-application\peer_t.py"'
    os.system(command)
    print("peer_t.py execution time for thread: 1 seconds")

# Run 100 instances of peer_t.py in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(run_peer_permenant) for _ in range(70)]
    # Wait for all threads to complete
    concurrent.futures.wait(futures)


def run_peer(i):
    start_time = time.time()
    os.system("python peer.py")
    end_time = time.time()
    execution_time = end_time - start_time
    times.append(execution_time)
    print(f"peer.py execution time for thread {i+1}: {execution_time} seconds")

times = []
num_executions = 1000

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(run_peer, i) for i in range(num_executions)]

    # Wait for all threads to complete
    concurrent.futures.wait(futures)

# Print the average execution time
avg_execution_time = sum(times) / num_executions
print(f"Average peer.py execution time: {avg_execution_time} seconds")

plt.plot(times)
plt.ylabel('Execution time (seconds)')
plt.xlabel('Execution number')
plt.show()