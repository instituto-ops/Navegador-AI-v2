import { WorkerManager } from './WorkerManager';

export class ModelProvider {
    /**
     * Sends complex or LLM generating requests to the cloud model (Puter.js)
     */
    static async processComplex(query: string, options?: any): Promise<string> {
        // @ts-ignore
        if (typeof puter === 'undefined') {
            throw new Error('Puter.js não carregado');
        }

        // @ts-ignore
        const response = await puter.ai.chat(query, { model: 'gpt-4o', ...options });

        return typeof response === 'string'
            ? response
            : (response?.message?.content || 'Sem resposta');
    }

    /**
     * Routes fast requests (scraping text vectorization or light vision) to the local Web Worker
     */
    static async processLocal(type: 'FEATURE_EXTRACTION' | 'VISION_PROCESS', data: any, onProgress?: (data: any) => void): Promise<any> {
        const workerManager = WorkerManager.getInstance();
        return await workerManager.process(type, data, onProgress);
    }
}
