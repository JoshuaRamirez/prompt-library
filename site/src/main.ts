import { SiteApplication } from './app.ts';

// start() = create() -> interconnect() -> activate() -> render()
new SiteApplication(document.getElementById('app')!).start();
