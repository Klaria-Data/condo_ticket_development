/**
 * Configuração de ambiente para desenvolvimento local.
 * useMock: true  → intercepta chamadas HTTP e retorna dados falsos (sem backend)
 * useMock: false → chama a API real servida pelo nginx na porta 8000
 */
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000',
  useMock: false,
};
