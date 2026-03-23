import uuid
from uuid import uuid4
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from app.database import Base


class FunnelProject(Base):
    """
    Stores the complete Vite + React SPA project as a JSONB file tree.
    This is what Sandpack reads on session open and writes on auto-save.
    Kept separate from funnels — different read/write patterns:
        funnels: queried constantly, small, metadata only
        funnel_projects: queried once per session open, ~80KB JSONB

    files object shape (Sandpack virtual file system):
    {
        "/package.json":             { "code": "..." },
        "/vite.config.ts":           { "code": "..." },
        "/tailwind.config.ts":       { "code": "..." },
        "/tsconfig.json":            { "code": "..." },
        "/index.html":               { "code": "..." },
        "/src/main.tsx":             { "code": "..." },
        "/src/App.tsx":              { "code": "..." },
        "/src/theme.ts":             { "code": "..." },  <- LLM-generated
        "/src/content.ts":           { "code": "..." },  <- LLM-generated
        "/src/pages/PreSell.tsx":    { "code": "..." },  <- LLM-generated
        "/src/pages/VSL.tsx":        { "code": "..." },  <- LLM-generated
        "/src/components/HeroSection.tsx": { "code": "..." },  <- boilerplate
        ...
    }

    node_modules intentionally excluded.
    Sandpack fetches dependencies from CDN using package.json at runtime.
    Option A: full self-contained snapshot including all boilerplate components.

    AUTO-SAVE pattern (surgical patch — never overwrite full object):
        UPDATE funnel_projects
        SET files = jsonb_set(files, $path, $new_content),
            updated_at = now()
        WHERE funnel_id = $funnel_id AND user_id = $user_id

    SESSION RESTORE:
        SELECT files FROM funnel_projects WHERE funnel_id = $1
        → pass directly to <SandpackProvider files={result.files}>
        → Sandpack boots environment exactly as user left it (~50ms)
    """

    __tablename__ = "funnel_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    funnel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("funnels.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="One project per funnel — unique enforced."
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalised for ownership checks"
    )
    files: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Complete Sandpack virtual file tree. ~80KB. node_modules excluded."
    )
    boilerplate_version: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="1.0.0",
        comment="Tracks which boilerplate version was used. For future migration tooling."
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_funnel_projects_funnel_id", "funnel_id", unique=True),
        Index("idx_funnel_projects_user_id", "user_id"),
    )