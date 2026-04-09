# AI Agent Guidelines

## Generation Guidelines

When generating a non-code file generate corresponding corrections file with the name *.corrections.md.

## File Organization

### Datasheets

- **Location**: `docs/datasheets/`
- **Format**: Keep original filenames from manufacturer/distributor
- **Parsed text**: Auto-saved to `.seb/datasheets/` (gitignored)

### AI-Generated Artifacts

- **Location**: `docs/ai/<topic>/`
- **Structure**: Group related analysis/audit/planning docs by topic
  - Example: `docs/ai/is31fl3741-audit/driver-audit.md`
  - Example: `docs/ai/drv2605l-implementation/plan.md`
- **Naming**: Use descriptive filenames (e.g., `driver-audit.md`, `register-map-comparison.md`)

### Plans

- **Location**: `docs/plan-*.md`
- **Archive**: Move completed plans to `docs/plans/<optional-topic>/*.md` when done. Unless multiple plans are related prefer to not use a topic.

## Commit Conventions

All commits follow prefixed [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

- ai generated commits will use the `ai@` prefix
- human written commits will use the `man@` prefix

## Error Documentation

### Documentation Corrections

**Location**: Same directory as the original file  
**Naming**: `<original-filename>.corrections.md`  
**Format**: `line(s) ####(-####): Correction`

**Example**: `docs/ai/is31fl3741-audit/driver-audit.corrections.md`

```markdown
line 42: PWM frequency register is 0x36, not 0x35 (Table 10, page 23)
lines 15-18: Scaling register default is 0xFF per datasheet section 8.2.3, not 0x00
line 67: Device supports 9 SW configurations, not 8 (missed Sw1Sw9 in Table 3)
```

### Code Corrections

**Process**:

1. AI commits code.
2. User commits fix.

**Examples:**

**AI commit example**:

```text
ai@<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Manual correction example**:

```text
man@<type>[optional scope]: correct <short-hash>

AI commit <short-hash> introduced <what was wrong>.

[body]

[optional footer(s)]
```
