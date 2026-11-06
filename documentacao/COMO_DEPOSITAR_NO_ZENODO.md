# Integração posterior GitHub–Zenodo

A preparação agora está organizada como um repositório público descompactado. O caminho recomendado é subir estes arquivos para um repositório GitHub público novo e habilitá-lo no Zenodo antes da primeira release. O projeto privado permanece separado.

1. Confirmar autoria, ORCIDs, licenças e descrição. Os metadados em `metadados/zenodo_rascunho.json` ainda são rascunho editorial.
2. Seguir `COMO_SUBIR_NO_GITHUB.md` na raiz. Enviar os arquivos e as pastas, sem um ZIP e sem histórico do projeto privado.
3. Habilitar a integração somente para o repositório público novo. Preparar metadados compatíveis com Zenodo antes de publicar a release.
4. Criar a release `v1.0.0` quando os responsáveis tiverem aprovado a publicação. Conferir o registro gerado pelo Zenodo e o conteúdo arquivado.
5. Acrescentar o DOI à citação do banco e ao README, identificando a versão efetivamente usada. O concept DOI é apropriado para referência geral ao conjunto de versões; a dissertação deve identificar a versão dos dados analisados.

Alternativamente, um depósito manual continua possível, mas não é necessário manter nesta pasta os ZIPs da preparação anterior. Os documentos oficiais integrais, tabelas e programas já estão organizados diretamente para versionamento. Nenhuma publicação foi feita por esta rotina de preparação.

Documentação oficial consultada em 6/11/2026: https://help.zenodo.org/docs/github/enable-repository/ ; https://help.zenodo.org/docs/github/archive-software/github-upload/ ; https://zenodo.org/help/versioning .
