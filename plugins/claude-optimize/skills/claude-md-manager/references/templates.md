# CLAUDE.md Templates

## Key Principles

- **Concise**: Dense, human-readable content; one line per concept when possible
- **Actionable**: Commands should be copy-paste ready
- **Project-specific**: Document patterns unique to this project, not generic advice
- **Current**: All info should reflect actual codebase state

## Recommended Sections

Use only the sections relevant to the project. Not all sections are needed.

### Commands
```markdown
## Commands

| Command | Description |
|---------|-------------|
| `<install command>` | Install dependencies |
| `<dev command>` | Start development server |
| `<build command>` | Production build |
| `<test command>` | Run tests |
| `<lint command>` | Lint/format code |
```

### Architecture
```markdown
## Architecture

```
<root>/
  <dir>/    # <purpose>
  <dir>/    # <purpose>
```
```

### Key Files
```markdown
## Key Files

- `<path>` - <purpose>
```

### Code Style
```markdown
## Code Style

- <convention>
- <preference over alternative>
```

### Environment
```markdown
## Environment

Required:
- `<VAR_NAME>` - <purpose>

Setup:
- <setup step>
```

### Testing
```markdown
## Testing

- `<test command>` - <what it tests>
- <testing convention or pattern>
```

### Gotchas
```markdown
## Gotchas

- <non-obvious thing that causes issues>
- <ordering dependency or prerequisite>
- <common mistake to avoid>
```

### Workflow
```markdown
## Workflow

- <when to do X>
- <preferred approach for Y>
```

## Template: Minimal
```markdown
# <Project Name>

<One-line description>

## Commands

| Command | Description |
|---------|-------------|
| `<command>` | <description> |

## Architecture

```
<structure>
```

## Gotchas

- <gotcha>
```

## Template: Comprehensive
```markdown
# <Project Name>

<One-line description>

## Commands

| Command | Description |
|---------|-------------|
| `<command>` | <description> |

## Architecture

```
<structure with descriptions>
```

## Key Files

- `<path>` - <purpose>

## Code Style

- <convention>

## Testing

- `<command>` - <scope>

## Gotchas

- <gotcha>
```

## Template: Package/Module

For packages within a monorepo or distinct modules.

```markdown
# <Package Name>

<Purpose of this package>

## Usage

```
<import/usage example>
```

## Key Exports

- `<export>` - <purpose>

## Dependencies

- `<dependency>` - <why needed>

## Notes

- <important note>
```

## Template: Monorepo
```markdown
# <Monorepo Name>

<Description>

## Packages

| Package | Description | Path |
|---------|-------------|------|
| `<name>` | <purpose> | `<path>` |

## Commands

| Command | Description |
|---------|-------------|
| `<command>` | <description> |

## Cross-Package Patterns

- <shared pattern>
```

## Update Principles

1. **Be specific**: Use actual file paths, real commands
2. **Be current**: Verify info against actual codebase
3. **Be brief**: One line per concept when possible
4. **Be useful**: Would this help a new Claude session?
