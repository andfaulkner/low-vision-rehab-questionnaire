// Extract text from PDFs with macOS's built-in PDFKit (no installs needed).
// Usage: osascript -l JavaScript pdfkit_extract.js IN1.pdf OUT1.txt [IN2.pdf OUT2.txt ...]
// Writes each page's text separated by "\f" (form feed), like pdftotext does,
// and prints one "pages<TAB>chars<TAB>in.pdf" line per file ("ERR<TAB>0<TAB>in.pdf" on failure).
ObjC.import('PDFKit');
ObjC.import('Foundation');

function run(argv) {
  const out = [];
  for (let i = 0; i + 1 < argv.length; i += 2) {
    const src = argv[i], dst = argv[i + 1];
    const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(src));
    if (doc.isNil() || doc.isLocked) { out.push(`ERR\t0\t${src}`); continue; }
    const n = doc.pageCount, pages = [];
    for (let p = 0; p < n; p++) {
      const s = doc.pageAtIndex(p).string;
      pages.push(s.isNil() ? '' : s.js);
    }
    const text = pages.join('\f');
    $(text).writeToFileAtomicallyEncodingError(dst, true, $.NSUTF8StringEncoding, null);
    out.push(`${n}\t${text.replace(/\s/g, '').length}\t${src}`);
  }
  return out.join('\n');
}
