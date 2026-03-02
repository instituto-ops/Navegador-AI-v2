type WorkerCallback = (data: any) => void;
type ResolveFn = (value: any) => void;
type RejectFn = (reason?: any) => void;

export class WorkerManager {
    private static instance: WorkerManager;
    private worker: Worker;
    private messageIdCounter: number = 0;
    private pendingRequests: Map<number, { resolve: ResolveFn; reject: RejectFn; onProgress?: WorkerCallback }> = new Map();

    private constructor() {
        this.worker = new Worker(new URL('../workers/aiWorker.ts', import.meta.url), { type: 'module' });

        this.worker.addEventListener('message', (event: MessageEvent) => {
            const { id, status, result, error, data } = event.data;

            const request = this.pendingRequests.get(id);
            if (!request) return;

            if (status === 'complete') {
                request.resolve(result);
                this.pendingRequests.delete(id);
            } else if (status === 'error') {
                request.reject(new Error(error));
                this.pendingRequests.delete(id);
            } else if (status === 'progress' && request.onProgress) {
                request.onProgress(data);
            }
        });
    }

    public static getInstance(): WorkerManager {
        if (!WorkerManager.instance) {
            WorkerManager.instance = new WorkerManager();
        }
        return WorkerManager.instance;
    }

    public process(type: 'FEATURE_EXTRACTION' | 'VISION_PROCESS', data: any, onProgress?: WorkerCallback): Promise<any> {
        return new Promise((resolve, reject) => {
            const id = ++this.messageIdCounter;
            this.pendingRequests.set(id, { resolve, reject, onProgress });
            this.worker.postMessage({ type, data, id });
        });
    }
}
