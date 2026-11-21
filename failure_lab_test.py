import sys, time
sys.path.insert(0, 'C:/AETHER')
from recovery.docker_recovery import DockerRecoveryEngine

e = DockerRecoveryEngine()

print("=== FAILURE LAB - AETHER Self-Healing Test ===")
print()
print("[1] Stopping EDGE-01 (simulating node failure)...")
result = e.stop_container("EDGE-01")
print("Stop result:", result)

print()
print("[2] Waiting 3 seconds...")
time.sleep(3)

print()
print("[3] Current node status:")
for n in e.get_edge_nodes():
    print(" ", n["node"], "|", n["status"])

print()
print("[4] Triggering AETHER auto-recovery on EDGE-01...")
recovery = e.restart_container("EDGE-01")
print("Recovery result:", recovery)

print()
print("[5] Final node status:")
for n in e.get_edge_nodes():
    print(" ", n["node"], "|", n["status"])
