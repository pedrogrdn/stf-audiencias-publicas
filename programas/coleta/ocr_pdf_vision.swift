#!/usr/bin/env swift

import AppKit
import Foundation
import PDFKit
import Vision

struct LinhaOCR {
    let texto: String
    let confianca: Float
    let x: CGFloat
    let topo: CGFloat
    let base: CGFloat
    let altura: CGFloat
}

struct PaginaOCR: Codable {
    let pagina_pdf: Int
    let texto: String
    let quantidade_linhas: Int
    let confianca_media: Double
}

struct DocumentoOCR: Codable {
    let mecanismo: String
    let idioma: String
    let arquivo_fonte: String
    let tamanho_fonte: Int64
    let paginas_pdf: Int
    let paginas_processadas: Int
    let palavras_customizadas: [String]
    let paginas: [PaginaOCR]
}

func mediana(_ valores: [CGFloat]) -> CGFloat {
    guard !valores.isEmpty else { return 0 }
    let ordenados = valores.sorted()
    let meio = ordenados.count / 2
    if ordenados.count.isMultiple(of: 2) {
        return (ordenados[meio - 1] + ordenados[meio]) / 2
    }
    return ordenados[meio]
}

func pareceTitulo(_ texto: String) -> Bool {
    let letras = texto.unicodeScalars.filter { CharacterSet.letters.contains($0) }
    guard letras.count >= 3 && texto.count <= 100 else { return false }
    let maiusculas = letras.filter { CharacterSet.uppercaseLetters.contains($0) }
    return Double(maiusculas.count) / Double(letras.count) >= 0.82
}

func juntarLinhas(_ linhas: [LinhaOCR]) -> String {
    guard !linhas.isEmpty else { return "" }
    let alturas = linhas.map(\.altura).filter { $0 > 0 }
    let alturaMediana = max(mediana(alturas), 0.008)
    let posicoesX = linhas.map(\.x).sorted()
    let indiceBase = min(posicoesX.count - 1, max(0, Int(Double(posicoesX.count) * 0.20)))
    let margemBase = posicoesX[indiceBase]

    var paragrafos: [String] = []
    var atual = ""
    var anterior: LinhaOCR?

    func encerrarParagrafo() {
        let limpo = atual.trimmingCharacters(in: .whitespacesAndNewlines)
        if !limpo.isEmpty { paragrafos.append(limpo) }
        atual = ""
    }

    for linha in linhas {
        var novoParagrafo = false
        if let anterior {
            let distanciaVertical = linha.topo - anterior.base
            let recuo = linha.x - margemBase
            let iniciouComRecuo = recuo > max(0.045, alturaMediana * 2.0)
                && linha.x - anterior.x > 0.025
            let separacaoVisual = distanciaVertical > max(0.010, alturaMediana * 0.75)
            novoParagrafo = iniciouComRecuo || separacaoVisual
                || pareceTitulo(linha.texto) || pareceTitulo(anterior.texto)
        }

        if novoParagrafo { encerrarParagrafo() }
        if atual.isEmpty {
            atual = linha.texto
        } else if atual.hasSuffix("-")
                    && linha.texto.first?.isLowercase == true {
            atual.removeLast()
            atual += linha.texto
        } else {
            atual += " " + linha.texto
        }
        anterior = linha
    }
    encerrarParagrafo()
    return paragrafos.joined(separator: "\n\n")
}

func reconhecerPagina(
    _ pagina: PDFPage,
    numero: Int,
    palavrasCustomizadas: [String]
) throws -> PaginaOCR {
    let limites = pagina.bounds(for: .cropBox)
    let escala: CGFloat = 1.5
    let tamanho = NSSize(
        width: max(1, limites.width * escala),
        height: max(1, limites.height * escala)
    )
    let miniatura = pagina.thumbnail(of: tamanho, for: .cropBox)
    var retangulo = NSRect(origin: .zero, size: miniatura.size)
    guard let imagemOriginal = miniatura.cgImage(forProposedRect: &retangulo, context: nil, hints: nil) else {
        throw NSError(domain: "OCRVision", code: 2, userInfo: [
            NSLocalizedDescriptionKey: "Não foi possível renderizar a página \(numero)."
        ])
    }
    let largura = imagemOriginal.width
    let altura = imagemOriginal.height
    let espacoCor = CGColorSpaceCreateDeviceRGB()
    guard let contexto = CGContext(
        data: nil,
        width: largura,
        height: altura,
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: espacoCor,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
        throw NSError(domain: "OCRVision", code: 3, userInfo: [
            NSLocalizedDescriptionKey: "Não foi possível normalizar a imagem da página \(numero)."
        ])
    }
    contexto.setFillColor(NSColor.white.cgColor)
    contexto.fill(CGRect(x: 0, y: 0, width: largura, height: altura))
    contexto.draw(imagemOriginal, in: CGRect(x: 0, y: 0, width: largura, height: altura))
    guard let imagem = contexto.makeImage() else {
        throw NSError(domain: "OCRVision", code: 4, userInfo: [
            NSLocalizedDescriptionKey: "Não foi possível concluir a imagem da página \(numero)."
        ])
    }

    let requisicao = VNRecognizeTextRequest()
    requisicao.recognitionLevel = .accurate
    requisicao.recognitionLanguages = ["pt-BR"]
    requisicao.usesLanguageCorrection = true
    requisicao.minimumTextHeight = 0.006
    requisicao.customWords = palavrasCustomizadas

    let manipulador = VNImageRequestHandler(cgImage: imagem, options: [:])
    do {
        try manipulador.perform([requisicao])
    } catch {
        // Alguns ambientes macOS não disponibilizam o modelo pt-BR para a
        // versão corrente do Vision. O reconhecimento latino padrão ainda é
        // preferível a abandonar integralmente um PDF sem camada textual.
        requisicao.recognitionLanguages = ["en-US"]
        requisicao.recognitionLevel = .fast
        try VNImageRequestHandler(cgImage: imagem, options: [:]).perform([requisicao])
    }
    let observacoes = requisicao.results ?? []
    var linhas: [LinhaOCR] = []
    for observacao in observacoes {
        guard let candidato = observacao.topCandidates(1).first else { continue }
        let texto = candidato.string.trimmingCharacters(in: .whitespacesAndNewlines)
        if texto.isEmpty || candidato.confidence < 0.12 { continue }
        let caixa = observacao.boundingBox
        linhas.append(LinhaOCR(
            texto: texto,
            confianca: candidato.confidence,
            x: caixa.minX,
            topo: 1.0 - caixa.maxY,
            base: 1.0 - caixa.minY,
            altura: caixa.height
        ))
    }
    linhas.sort {
        if abs($0.topo - $1.topo) < max($0.altura, $1.altura) * 0.45 {
            return $0.x < $1.x
        }
        return $0.topo < $1.topo
    }
    let confianca = linhas.isEmpty
        ? 0
        : Double(linhas.map(\.confianca).reduce(0, +)) / Double(linhas.count)
    return PaginaOCR(
        pagina_pdf: numero,
        texto: juntarLinhas(linhas),
        quantidade_linhas: linhas.count,
        confianca_media: confianca
    )
}

guard CommandLine.arguments.count >= 3 else {
    FileHandle.standardError.write(Data(
        "Uso: ocr_pdf_vision.swift entrada.pdf saida.json [limite_paginas]\n".utf8
    ))
    exit(2)
}

let entrada = URL(fileURLWithPath: CommandLine.arguments[1])
let saida = URL(fileURLWithPath: CommandLine.arguments[2])
let limiteInformado = CommandLine.arguments.count >= 4 ? Int(CommandLine.arguments[3]) : nil
let limite = (limiteInformado ?? 0) > 0 ? limiteInformado : nil
let arquivoPalavras = CommandLine.arguments.count >= 5
    ? URL(fileURLWithPath: CommandLine.arguments[4])
    : nil
let palavrasCustomizadas: [String]
if let arquivoPalavras,
   let conteudo = try? String(contentsOf: arquivoPalavras, encoding: .utf8) {
    palavrasCustomizadas = Array(Set(
        conteudo.components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    )).sorted()
} else {
    palavrasCustomizadas = ["Audiência Pública", "Audiência Pública - Saúde"]
}

guard let documento = PDFDocument(url: entrada) else {
    FileHandle.standardError.write(Data("Não foi possível abrir o PDF.\n".utf8))
    exit(3)
}

let atributos = try FileManager.default.attributesOfItem(atPath: entrada.path)
let tamanhoFonte = (atributos[.size] as? NSNumber)?.int64Value ?? 0
let paginasParaProcessar = min(documento.pageCount, limite ?? documento.pageCount)
var paginas: [PaginaOCR] = []
paginas.reserveCapacity(paginasParaProcessar)

for indice in 0..<paginasParaProcessar {
    guard let pagina = documento.page(at: indice) else { continue }
    FileHandle.standardError.write(Data(
        "OCR \(entrada.lastPathComponent): página \(indice + 1)/\(paginasParaProcessar)\n".utf8
    ))
    do {
        let resultado = try autoreleasepool {
            try reconhecerPagina(
                pagina,
                numero: indice + 1,
                palavrasCustomizadas: palavrasCustomizadas
            )
        }
        paginas.append(resultado)
    } catch {
        let erro = error as NSError
        let mensagem = "Falha no OCR da página \(indice + 1): domínio=\(erro.domain) "
            + "código=\(erro.code) descrição=\(erro.localizedDescription) "
            + "dados=\(erro.userInfo)\n"
        FileHandle.standardError.write(Data(mensagem.utf8))
        exit(4)
    }
}

let resultado = DocumentoOCR(
    mecanismo: "Apple Vision - reconhecimento preciso",
    idioma: "pt-BR",
    arquivo_fonte: entrada.lastPathComponent,
    tamanho_fonte: tamanhoFonte,
    paginas_pdf: documento.pageCount,
    paginas_processadas: paginas.count,
    palavras_customizadas: palavrasCustomizadas,
    paginas: paginas
)
let codificador = JSONEncoder()
codificador.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
let dados = try codificador.encode(resultado)
try FileManager.default.createDirectory(
    at: saida.deletingLastPathComponent(),
    withIntermediateDirectories: true
)
try dados.write(to: saida, options: .atomic)
