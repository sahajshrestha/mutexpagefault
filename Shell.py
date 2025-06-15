import collections
import random
import time
from multiprocessing import Process, Semaphore, Lock, current_process, Manager

# --- Memory Management with Paging ---

class Page:
    def __init__(self, process_id, page_id):
        self.process_id = process_id
        self.page_id = page_id

    def __str__(self):
        return f"P{self.process_id}-Pg{self.page_id}"

class PagingSystem:
    def __init__(self, num_frames, algorithm='FIFO'):
        self.num_frames = num_frames
        self.frames = []
        self.page_table = {}
        self.algorithm = algorithm
        self.access_order = collections.deque()
        self.page_faults = 0
        self.memory_usage = {}  # Tracks how many pages each process has in memory

    def request_page(self, process_id, page_id):
        key = (process_id, page_id)
        print(f"\n[REQUEST] Process {process_id} requests page {page_id}")
        if key in self.page_table:
            print(f"[HIT] {key}")
            if self.algorithm == 'LRU':
                self.access_order.remove(key)
                self.access_order.append(key)
        else:
            print(f"[FAULT] {key}")
            self.page_faults += 1
            if len(self.frames) >= self.num_frames:
                self.replace_page()
            new_page = Page(process_id, page_id)
            self.frames.append(new_page)
            self.page_table[key] = new_page
            self.access_order.append(key)
            self.memory_usage[process_id] = self.memory_usage.get(process_id, 0) + 1
        self.display_frames()

    def replace_page(self):
        key = self.access_order.popleft()
        self.frames = [f for f in self.frames if (f.process_id, f.page_id) != key]
        del self.page_table[key]
        self.memory_usage[key[0]] -= 1
        if self.memory_usage[key[0]] == 0:
            del self.memory_usage[key[0]]
        print(f"[REPLACE] Evicted page: {key}")

    def display_frames(self):
        print("Memory Frames:", [str(f) for f in self.frames])
        print("Current Usage:", self.memory_usage)

    def stats(self):
        return self.page_faults, len(self.frames), self.memory_usage

# --- Process Synchronization: Producer-Consumer ---

def producer(buffer, empty, full, mutex, pid, count):
    for _ in range(count):
        time.sleep(random.uniform(0.1, 0.5))
        item = random.randint(1, 100)
        empty.acquire()
        mutex.acquire()
        buffer.append(item)
        print(f"[Producer {pid}] Produced {item} | Buffer: {list(buffer)}")
        mutex.release()
        full.release()

def consumer(buffer, empty, full, mutex, cid, count):
    for _ in range(count):
        time.sleep(random.uniform(0.1, 0.5))
        full.acquire()
        mutex.acquire()
        item = buffer.pop(0)
        print(f"[Consumer {cid}] Consumed {item} | Buffer: {list(buffer)}")
        mutex.release()
        empty.release()

# --- Combined Simulation ---

def simulate_memory_access(paging_system, access_pattern, title="Memory Management Simulation"):
    print(f"\n--- {title} ({paging_system.algorithm}) ---")
    for pid, page in access_pattern:
        paging_system.request_page(pid, page)
        time.sleep(0.1)
    pf, used, mem_usage = paging_system.stats()
    print(f"\nTotal Page Faults: {pf}, Memory Frames Used: {used}")
    print("Final Memory Usage per Process:", mem_usage)

def simulate_producer_consumer():
    print("\n--- Producer-Consumer Synchronization ---")
    manager = Manager()
    buffer = manager.list()
    buffer_size = 5

    empty = Semaphore(buffer_size)
    full = Semaphore(0)
    mutex = Lock()

    p = Process(target=producer, args=(buffer, empty, full, mutex, 1, 5))
    c = Process(target=consumer, args=(buffer, empty, full, mutex, 1, 5))

    p.start()
    c.start()
    p.join()
    c.join()

# --- Main Function ---

if __name__ == "__main__":
    access_pattern = [(1, 0), (1, 1), (2, 0), (1, 0), (3, 1), (1, 2), (2, 1), (3, 0)]

    # FIFO Simulation
    fifo_system = PagingSystem(num_frames=3, algorithm='FIFO')
    simulate_memory_access(fifo_system, access_pattern, "FIFO Page Replacement")

    # LRU Simulation
    lru_system = PagingSystem(num_frames=3, algorithm='LRU')
    simulate_memory_access(lru_system, access_pattern, "LRU Page Replacement")

    # Synchronization Simulation
    simulate_producer_consumer()
