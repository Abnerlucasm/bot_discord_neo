# Desenvolvimento e testes do Glassfish

Este guia descreve o modo de desenvolvimento e os comandos disponíveis para testar o gerenciamento dos serviços.

## Modo de desenvolvimento

Ative o modo antes de realizar testes:

```text
/modo_desenvolvimento_glassfish ativar:true
```

O comando aplica estas configurações:

| Configuração | Produção | Desenvolvimento |
| --- | ---: | ---: |
| Tempo máximo de uso | 24 horas | 1 hora |
| Intervalo de verificação | 15 minutos | 1 minuto |
| Intervalo de lembretes | 2 horas | 1 hora |
| Máximo de extensões | 3 | 2 |

Para restaurar os valores de produção:

```text
/modo_desenvolvimento_glassfish ativar:false
```

## Comandos de teste

Todos os comandos desta seção exigem o cargo de TI.

### Simular tempo de uso

```text
/simular_tempo_glassfish servico_id:97-1 horas_atras:3
```

O serviço precisa estar em uso. O comando altera o horário inicial e reinicia os dados de lembrete e extensão. Uma verificação posterior pode enviar um lembrete ou liberar o serviço se o timeout tiver expirado.

### Preparar um teste de lembrete

```text
/testar_lembrete_glassfish simular_tempo:3
```

O comando lista os serviços em uso e permite escolher um para simular o tempo informado. Ele não envia a DM por conta própria. Para executar a verificação imediatamente, use:

```text
/verificacao_forcada_glassfish
```

A verificação pode enviar uma DM ao usuário associado ao serviço ou liberá-lo se o timeout tiver expirado. Use um serviço de teste e confirme seu estado antes de executar a verificação.

### Testar envio direto de DM

```text
/testar_envio_lembrete_glassfish
```

O comando seleciona o primeiro serviço em uso e envia uma DM de teste ao usuário associado. Se o serviço não tiver um `user_id` válido, o comando retorna um erro. O envio não altera o estado do serviço, mas os botões da DM continuam ligados ao serviço real.

### Consultar o estado do serviço

```text
/status_servico_glassfish servico_id:97-1
```

A resposta mostra o status, o usuário associado, o tempo de uso, as extensões, os últimos checks e lembretes e as próximas ações previstas.

## Fluxo de teste recomendado

1. Faça backup de `config.json` e `services.json`.
2. Ative o modo de desenvolvimento.
3. Use um serviço de teste pelo comando `/glassfish`.
4. Simule o tempo de uso ou prepare um teste de lembrete.
5. Consulte o estado do serviço.
6. Execute `/verificacao_forcada_glassfish` quando quiser processar o cenário imediatamente.
7. Confira o estado do serviço, as DMs e os logs.
8. Desative o modo de desenvolvimento.

A simulação modifica dados reais de `services.json`. O comando de verificação pode enviar notificações ou liberar o serviço, então evite usar serviços de produção nesses cenários.

## Configurar timeouts

O comando `/configurar_timeout_glassfish` aceita os parâmetros abaixo. Informe ao menos um para salvar uma alteração.

| Parâmetro | Limite | Unidade |
| --- | ---: | --- |
| `horas` | 1 a 168 | horas |
| `intervalo_verificacao` | 5 a 60 | minutos |
| `intervalo_lembrete` | 1 a 12 | horas |
| `max_extensoes` | 1 a 10 | extensões |

Exemplo:

```text
/configurar_timeout_glassfish horas:24 intervalo_verificacao:15 intervalo_lembrete:2 max_extensoes:3
```

## Relatório e logs

O comando `/relatorio_glassfish` mostra serviços em uso, duração, última confirmação, último lembrete, lembretes sem resposta e percentuais de disponibilidade e uso. O comando não apresenta histórico de liberações ou métricas agregadas de extensões.

Os logs registram as verificações, notificações, liberações e ações administrativas. Consulte os logs quando um comando ou uma interação falhar.

## Solução de problemas

### Lembretes não chegam

1. Verifique se o bot pode enviar mensagens diretas ao usuário associado ao serviço.
2. Confirme que o serviço está em uso e tem um `user_id` válido em `services.json`.
3. Use `/testar_envio_lembrete_glassfish` e confira os logs.

### Verificação não funciona

1. Confirme que o bot está conectado.
2. Execute `/verificacao_forcada_glassfish`.
3. Confira os valores de timeout com `/obter_timeout_glassfish`.

### Componentes não respondem

1. Verifique se a interação não expirou.
2. Confirme se o serviço ainda está cadastrado.
3. Confira as permissões do bot e do usuário.

Consulte o [README principal](../README.md) para conhecer a estrutura do projeto e as camadas do Glassfish.
