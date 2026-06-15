/**
 * Configuração de ambiente para produção.
 * A apiUrl é vazia porque o nginx serve o frontend e a API na mesma origem,
 * evitando problemas de CORS e hardcoded de hostname em produção.
 */
export const environment = {
  production: true,
  apiUrl: '',
  useMock: false,
};
