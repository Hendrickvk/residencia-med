// Prepara a foto de perfil no navegador, antes de enviar.
//
// O recorte e a redução acontecem aqui e não no servidor porque o servidor não
// tem biblioteca de imagem — e não precisa ganhar uma só por isto. O que ele
// faz é o que não dá para delegar ao cliente: conferir tamanho e assinatura do
// arquivo, já que quem chama a API pode ser qualquer coisa, não só esta tela.

export const LADO = 256;
export const MIME_SAIDA = "image/jpeg";

export class FotoInvalida extends Error {}

/** Recorta no centro, reduz para 256×256 e devolve base64 (sem o prefixo
 *  `data:`). 256 porque o avatar tem 36px e ainda fica nítido em tela retina
 *  com folga; o resultado costuma ficar em 20–40 KB, longe do teto do
 *  servidor. */
export async function prepararFoto(arquivo: File): Promise<string> {
  if (!arquivo.type.startsWith("image/")) {
    throw new FotoInvalida("Escolha um arquivo de imagem.");
  }
  // `createImageBitmap` decodifica fora da thread principal e entende tudo o
  // que o navegador abre — inclusive HEIC no Safari, que é o que sai da câmera
  // do iPhone e não sobreviveria a um `<img src>` em outros navegadores.
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(arquivo);
  } catch {
    throw new FotoInvalida("Não foi possível abrir essa imagem.");
  }

  const canvas = document.createElement("canvas");
  canvas.width = LADO;
  canvas.height = LADO;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new FotoInvalida("Não foi possível preparar a imagem.");

  // Recorte quadrado pelo centro: o avatar é um círculo, e esticar a imagem
  // para caber deformaria o rosto.
  const lado = Math.min(bitmap.width, bitmap.height);
  const x = (bitmap.width - lado) / 2;
  const y = (bitmap.height - lado) / 2;
  ctx.drawImage(bitmap, x, y, lado, lado, 0, 0, LADO, LADO);
  bitmap.close();

  const dataUrl = canvas.toDataURL(MIME_SAIDA, 0.85);
  return dataUrl.split(",")[1];
}
