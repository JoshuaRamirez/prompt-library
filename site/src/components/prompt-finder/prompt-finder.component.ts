import { Component } from 'vanilla-mvc';
import { PromptFinderController } from './prompt-finder.controller.ts';
import type { PromptFinderModel } from './prompt-finder.model.ts';
import { promptFinderTemplate } from './prompt-finder.template.ts';

export class PromptFinderComponent extends Component<PromptFinderModel, PromptFinderController> {
  protected createTemplate() { return promptFinderTemplate; }
  protected createController() { return new PromptFinderController(); }
}
