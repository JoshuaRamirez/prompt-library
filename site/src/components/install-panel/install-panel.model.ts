/** What the install-panel view reads. */
export interface InstallPanelModel {
  /** Each command as its words, so a line breaks only between them. */
  commands: readonly (readonly string[])[];
  copyLabel: string;
}
