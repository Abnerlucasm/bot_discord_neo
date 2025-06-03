# Guia de Desenvolvimento e Testes - Sistema Glassfish

Este documento descreve as funcionalidades de desenvolvimento e teste implementadas no sistema Glassfish do Bot Discord Neo.

## 🧪 Modo de Desenvolvimento

O sistema inclui um modo de desenvolvimento especial que reduz drasticamente os tempos de timeout para facilitar testes.

### Ativação do Modo de Desenvolvimento

```bash
/modo_desenvolvimento_glassfish ativar:True
```

### Configurações do Modo de Desenvolvimento

| Configuração | Produção | Desenvolvimento |
|--------------|----------|-----------------|
| Tempo máximo de uso | 24 horas | 2 horas |
| Intervalo de verificação | 15 minutos | 1 minuto |
| Intervalo de lembretes | 2 horas | 1 hora |
| Máximo de extensões | 3 | 2 |

### Desativação

```bash
/modo_desenvolvimento_glassfish ativar:False
```

## 🛠️ Comandos de Teste

### 1. Simulação de Tempo de Uso

Simula que um serviço está em uso há X horas:

```bash
/simular_tempo_glassfish servico_id:97-1 horas_atras:3
```

**Pré-requisitos:**
- Serviço deve estar em uso
- Apenas usuários com cargo de TI

**Funcionalidade:**
- Altera o timestamp de início de uso
- Permite testar cenários de timeout sem esperar tempo real
- Útil para testar liberação automática

### 2. Status Detalhado de Serviço

Mostra informações completas sobre um serviço específico:

```bash
/status_servico_glassfish servico_id:97-1
```

**Informações Exibidas:**
- Status atual (disponível/em uso)
- Usuário atual (se em uso)
- Tempo total de uso
- Número de extensões utilizadas
- Timestamps de última verificação e lembrete
- Analytics detalhados

### 3. Teste de Lembretes

Testa o sistema de lembretes com serviços em uso:

```bash
/testar_lembrete_glassfish simular_tempo:3
```

**Funcionalidade:**
- Lista serviços em uso
- Permite selecionar serviço para teste
- Simula tempo de uso especificado
- Força envio de lembrete

### 4. Teste Direto de DM

Testa o envio de mensagem direta:

```bash
/testar_envio_lembrete_glassfish
```

**Funcionalidade:**
- Envia lembrete de teste para o usuário que executa
- Verifica se DMs estão funcionando
- Não afeta serviços reais

## 🔄 Fluxo de Testes Recomendado

### Teste Completo do Sistema

1. **Preparação:**
   ```bash
   /modo_desenvolvimento_glassfish ativar:True
   ```

2. **Usar um serviço:**
   - Execute `/glassfish`
   - Selecione um serviço e clique em "Usar"

3. **Simular tempo:**
   ```bash
   /simular_tempo_glassfish servico_id:97-1 horas_atras:2
   ```

4. **Verificar status:**
   ```bash
   /status_servico_glassfish servico_id:97-1
   ```

5. **Forçar verificação:**
   ```bash
   /verificacao_forcada_glassfish
   ```

6. **Verificar se lembrete foi enviado**
   - Confira suas DMs
   - Teste os botões de resposta

7. **Finalização:**
   ```bash
   /modo_desenvolvimento_glassfish ativar:False
   ```

### Teste de Liberação Automática

1. **Configurar tempo muito baixo:**
   ```bash
   /configurar_timeout_glassfish horas:1 intervalo_lembrete:1
   ```

2. **Usar serviço e simular:**
   ```bash
   /simular_tempo_glassfish servico_id:97-1 horas_atras:2
   ```

3. **Forçar verificação:**
   ```bash
   /verificacao_forcada_glassfish
   ```

4. **Verificar liberação automática nos logs**

## 📊 Monitoramento e Debug

### Relatório Completo

```bash
/relatorio_glassfish
```

**Informações Incluídas:**
- Serviços em uso com detalhes temporais
- Lembretes pendentes de resposta
- Liberações automáticas das últimas 24h
- Estatísticas de uso
- Analytics de extensões

### Logs do Sistema

Os logs são gerados automaticamente e incluem:
- Verificações de timeout
- Envio de lembretes
- Liberações automáticas
- Ações administrativas
- Erros e exceções

### Canais de Notificação

- **Canal de Logs:** Todas as ações são registradas
- **DMs para Usuários:** Lembretes e notificações
- **Mensagem Persistente:** Atualizada automaticamente

## ⚠️ Cuidados e Limitações

### Ambiente de Desenvolvimento

- **Não usar em produção** com modo de desenvolvimento ativo
- **Tempos reduzidos** podem causar liberações prematuras
- **Testes frequentes** podem gerar spam de notificações

### Simulação de Tempo

- **Irreversível:** Uma vez simulado, não pode ser desfeito
- **Afeta verificações:** Pode triggerar liberações automáticas
- **Use com cuidado:** Apenas em ambiente de teste

### Backup de Configurações

Antes de testes intensivos:
1. Faça backup de `services.json`
2. Faça backup de `config.json`
3. Documente configurações atuais

## 🔧 Troubleshooting

### Lembretes não chegam

1. Verificar se o bot pode enviar DMs
2. Testar com `/testar_envio_lembrete_glassfish`
3. Verificar logs para erros

### Verificação não funciona

1. Verificar se o loop está ativo
2. Usar `/verificacao_forcada_glassfish`
3. Verificar configurações de interval

### Botões não respondem

1. Verificar se a interação não expirou
2. Verificar se o serviço ainda existe
3. Verificar permissões do usuário

## 📈 Métricas e Analytics

O sistema coleta automaticamente:
- Tempo médio de uso por serviço
- Número de extensões solicitadas
- Taxa de resposta a lembretes
- Frequência de liberações automáticas

Essas métricas são visíveis no relatório detalhado gerado pelo comando `/relatorio_glassfish`.

## 🎯 Casos de Uso para Testes

### Cenário 1: Usuário Responsivo
- Usuário usa serviço
- Recebe lembrete
- Confirma uso rapidamente

### Cenário 2: Usuário Não Responsivo
- Usuário usa serviço
- Recebe lembrete
- Não responde
- Sistema libera automaticamente

### Cenário 3: Múltiplas Extensões
- Usuário usa serviço
- Confirma múltiplas vezes
- Atinge limite de extensões
- Sistema libera automaticamente

### Cenário 4: Administração
- TI adiciona/remove serviços
- TI força liberação de todos
- TI monitora relatórios

Este guia deve ser usado em conjunto com a documentação principal (README.md) para desenvolvimento e manutenção eficazes do sistema. 