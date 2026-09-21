    // Hosted dictionary data is compressed losslessly; registrations and IDs stay unchanged.
    if (/^shards\/[a-z_]{2}\.js$/.test(relativePath)) {
      return (async () => {
        if (typeof DecompressionStream !== 'function') {
          throw error('当前浏览器版本较旧，请更新浏览器后使用站内词典。');
        }
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
        try {
          const url = new URL(relativePath.replace(/\.js$/, '.json.gz.bin'), directory);
          const response = await fetch(url, {signal: controller.signal, credentials: 'same-origin'});
          if (!response.ok) throw new Error('HTTP ' + response.status);
          const bytes = new Uint8Array(await response.arrayBuffer());
          // Some hosts apply Content-Encoding and the browser decompresses first.
          const payload = bytes[0] === 0x1f && bytes[1] === 0x8b
            ? new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')))
            : new Response(bytes);
          const data = await payload.json();
          registerShard(relativePath.slice(7, 9), data);
          if (!registered()) throw new Error('Dictionary version mismatch');
        } catch (problem) {
          console.warn('Dictionary asset could not load:', relativePath, problem.name, problem.message);
          throw error('词典数据未能加载，请检查网络后重试。', problem);
        } finally {
          clearTimeout(timer);
        }
      })();
    }
