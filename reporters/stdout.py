from queue import Queue
from models.models import Event


class StdoutReporter:
    def subscribe(self, queue: Queue):
        while True:
            event: Event = queue.get()
            print(event.model_dump_json())
