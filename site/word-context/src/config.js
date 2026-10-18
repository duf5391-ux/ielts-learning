// The module can be hosted at /word-context/ without importing the host application's code.
export const config = Object.freeze({
  hostEntry: 'https://duf5391-ux.github.io/ielts-learning/',
  storagePrefix: 'word-context:v1:',
  collectionPath: new URL('../data/words.json',import.meta.url).href,
});
