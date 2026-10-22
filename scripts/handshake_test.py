import sys
import grpc

from google.protobuf.empty_pb2 import Empty


SOCKET = "unix:///run/containerd/containerd.sock"

sys.path.insert(0, "../app/runtime/containerd_api")

from app.runtime.containerd_api.services.version.v1.version_pb2_grpc import VersionStub
from app.runtime.containerd_api.services.containers.v1.containers_pb2_grpc import ContainersStub


def main() -> int:
    channel = grpc.insecure_channel(SOCKET)
    grpc.channel_ready_future(channel).result(timeout=5)

    v = VersionStub(channel)
    resp = v.Version(Empty(), timeout=5)
    print(f"Containerd version: {resp.version}, revision: {resp.revision}")

    c = ContainersStub(channel)
    containers = c.List(_empty_list_request(), timeout=5, metadata=[("containerd-namespace", "default")])
    print(f"containers in store: {len(containers.containers)}")
    return 0


def _empty_list_request():
    from app.runtime.containerd_api.services.containers.v1.containers_pb2 import ListContainersRequest
    return ListContainersRequest()


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except grpc.RpcError as e:
        print(f"gRPC error: {e.code()} - {e.details()}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
