import { pipeline, env } from '@xenova/transformers';

// Configuration: run in browser, use cache, disable local Node.js models
env.allowLocalModels = false;
env.useBrowserCache = true;

class PipelineSingleton {
  static taskName: any = 'feature-extraction';
  static modelName = 'Xenova/all-MiniLM-L6-v2';
  static instance: any = null;

  static async getInstance(progress_callback?: Function) {
    if (this.instance === null) {
      this.instance = await pipeline(this.taskName, this.modelName, { progress_callback });
    }
    return this.instance;
  }
}

class VisionPipelineSingleton {
    static taskName: any = 'image-classification';
    static modelName = 'Xenova/vit-base-patch16-224';
    static instance: any = null;

    static async getInstance(progress_callback?: Function) {
        if (this.instance === null) {
            this.instance = await pipeline(this.taskName, this.modelName, { progress_callback });
        }
        return this.instance;
    }
}

self.addEventListener('message', async (event: MessageEvent) => {
    const { type, data, id } = event.data;

    try {
        if (type === 'FEATURE_EXTRACTION') {
            const extractor = await PipelineSingleton.getInstance((x: any) => {
                self.postMessage({ id, status: 'progress', data: x });
            });
            const output = await extractor(data.text, { pooling: 'mean', normalize: true });
            self.postMessage({ id, status: 'complete', type: 'FEATURE_EXTRACTION', result: Array.from(output.data) });
        } else if (type === 'VISION_PROCESS') {
            const classifier = await VisionPipelineSingleton.getInstance((x: any) => {
                 self.postMessage({ id, status: 'progress', data: x });
            });
            const output = await classifier(data.image);
            self.postMessage({ id, status: 'complete', type: 'VISION_PROCESS', result: output });
        } else {
             self.postMessage({ id, status: 'error', error: `Unknown type: ${type}` });
        }
    } catch (err: any) {
        self.postMessage({ id, status: 'error', error: err.message });
    }
});
