import { Plugin, Notice, TFile } from 'obsidian';

interface ClipperSettings {
	bridgeUrl: string;
}

const DEFAULT_SETTINGS: ClipperSettings = {
	bridgeUrl: 'http://127.0.0.1:8088'
}

export default class HermesClipperPlugin extends Plugin {
	settings: ClipperSettings;

	async onload() {
		await this.loadSettings();

		this.addCommand({
			id: 'hermes-synthesize-current',
			name: 'Synthesize Current Note',
			callback: () => this.synthesizeNote()
		});
	}

	async synthesizeNote() {
		const activeFile = this.app.workspace.getActiveFile();
		if (!(activeFile instanceof TFile)) {
			new Notice('No active file to synthesize.');
			return;
		}

		new Notice(`Dispatching Hermes to synthesize: ${activeFile.name}...`);

		try {
			// Note: This requires the bridge server to be running.
			const response = await fetch(`${this.settings.bridgeUrl}/agent/synthesize`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					path: activeFile.path, // Bridge needs absolute path if possible, or vault relative
					prompt: "Synthesize and refine this note."
				})
			});

			const data = await response.json();
			if (data.status === 'success') {
				new Notice('Synthesis complete! Hermes is updating your vault.');
			} else {
				new Notice('Hermes failed: ' + data.message);
			}
		} catch (err) {
			new Notice('Failed to connect to Hermes Bridge.');
			console.error(err);
		}
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}
}
