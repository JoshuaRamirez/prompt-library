import { Component } from 'vanilla-mvc';
import { PromptComposerController } from './prompt-composer.controller.ts';
import type { PromptComposerModel } from './prompt-composer.model.ts';
import { promptComposerTemplate } from './prompt-composer.template.ts';

export class PromptComposerComponent extends Component<PromptComposerModel, PromptComposerController> {
  protected createTemplate() { return promptComposerTemplate; }
  protected createController() { return new PromptComposerController(); }
}
