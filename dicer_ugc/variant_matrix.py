"""Generate variant task matrix from configuration."""

from typing import List, Optional
import hashlib
from pathlib import Path

from .config import PipelineConfig
from .models import VariantTask, VariantType
from .utils import read_script_content, log_info, console
from rich.table import Table


class VariantMatrixBuilder:
    """Builds deterministic task matrix for video generation."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.base_script = self._load_base_script()
    
    def _load_base_script(self) -> str:
        """Load the reference script content."""
        return read_script_content(self.config.reference.script)
    
    def _generate_task_id(self, actor_id: str, variant_type: str, variant_num: int) -> str:
        """Generate deterministic task ID."""
        content = f"{self.config.offer_id}_{actor_id}_{variant_type}_{variant_num}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_modified_script(self, actor_id: str, variant_num: int) -> str:
        """
        Generate a modified script variant.
        
        Note: This is a placeholder that returns the base script.
        In production, this would call an LLM to generate variations.
        """
        # TODO: Implement LLM-based script modification
        # For now, append variant marker to demonstrate the concept
        return f"{self.base_script}\n\n[Variant {variant_num} for {actor_id}]"
    
    def build_matrix(self) -> List[VariantTask]:
        """Build the complete task matrix."""
        tasks = []
        
        for actor_id in self.config.actors:
            # Task 0: Identical script
            if self.config.variants.identical_script:
                task = VariantTask(
                    task_id=self._generate_task_id(actor_id, "identical", 0),
                    actor_id=actor_id,
                    variant_type=VariantType.IDENTICAL,
                    variant_num=0,
                    script_text=self.base_script
                )
                tasks.append(task)
            
            # Tasks 1-n: Modified scripts
            for variant_num in range(1, self.config.variants.minor_script_variants + 1):
                script_text = self._generate_modified_script(actor_id, variant_num)
                task = VariantTask(
                    task_id=self._generate_task_id(actor_id, "modified", variant_num),
                    actor_id=actor_id,
                    variant_type=VariantType.MODIFIED,
                    variant_num=variant_num,
                    script_text=script_text
                )
                tasks.append(task)
        
        log_info(f"Generated {len(tasks)} variant tasks")
        return tasks
    
    def display_matrix(self, tasks: List[VariantTask]) -> None:
        """Display the task matrix in a table."""
        table = Table(title=f"Variant Matrix for {self.config.offer_id}")
        table.add_column("Task ID", style="cyan")
        table.add_column("Actor", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Variant #", justify="right")
        table.add_column("Output File", style="dim")
        
        for task in tasks:
            table.add_row(
                task.task_id,
                task.actor_id,
                task.variant_type.value,
                str(task.variant_num),
                task.output_filename
            )
        
        console.print(table)
    
    def get_task_by_id(self, task_id: str, tasks: Optional[List[VariantTask]] = None) -> Optional[VariantTask]:
        """Find a specific task by ID."""
        if tasks is None:
            tasks = self.build_matrix()
        
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_tasks_for_actor(self, actor_id: str, tasks: Optional[List[VariantTask]] = None) -> List[VariantTask]:
        """Get all tasks for a specific actor."""
        if tasks is None:
            tasks = self.build_matrix()
        
        return [task for task in tasks if task.actor_id == actor_id]
    
    def get_resume_tasks(self, completed_task_ids: List[str]) -> List[VariantTask]:
        """Get tasks that haven't been completed yet."""
        all_tasks = self.build_matrix()
        return [task for task in all_tasks if task.task_id not in completed_task_ids]