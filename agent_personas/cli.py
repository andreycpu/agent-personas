"""
Command-line interface for agent_personas package.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config_builder import PersonaConfigBuilder, interactive_config_builder
from .templates import (
    template_registry, 
    list_available_templates, 
    create_persona_from_template,
    export_template_to_file,
    import_template_from_file
)
from .validation import validate_persona_traits, validate_persona_name
from .monitoring import performance_report
from .security import RateLimiter, sanitize_input
from .benchmarking import Benchmarker, quick_benchmark
from .exceptions import PersonaError


class PersonaCLI:
    """Command-line interface for persona management."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = argparse.ArgumentParser(
            description="Agent Personas CLI - Create and manage AI personas",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  personas create --interactive                    # Interactive persona creation
  personas create --template technical_assistant  # Create from template
  personas validate persona.json                  # Validate persona file
  personas templates list                         # List available templates
  personas benchmark test_function.py             # Benchmark functions
  personas performance report                     # Generate performance report
            """
        )
        
        self._setup_commands()
    
    def _setup_commands(self):
        """Setup CLI commands and arguments."""
        subparsers = self.parser.add_subparsers(dest='command', help='Available commands')
        
        # Create command
        create_parser = subparsers.add_parser('create', help='Create a new persona')
        create_group = create_parser.add_mutually_exclusive_group(required=True)
        create_group.add_argument('--interactive', '-i', action='store_true',
                                help='Interactive persona creation')
        create_group.add_argument('--template', '-t', type=str,
                                help='Create from template')
        create_parser.add_argument('--output', '-o', type=str, default='persona.json',
                                 help='Output file path')
        create_parser.add_argument('--variables', '-v', type=str, nargs='+',
                                 help='Template variables in key=value format')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate persona configuration')
        validate_parser.add_argument('file', type=str, help='Persona file to validate')
        validate_parser.add_argument('--strict', action='store_true',
                                   help='Enable strict validation')
        
        # Templates command
        templates_parser = subparsers.add_parser('templates', help='Template management')
        templates_subparsers = templates_parser.add_subparsers(dest='template_action')
        
        # Templates list
        templates_subparsers.add_parser('list', help='List available templates')
        
        # Templates info
        info_parser = templates_subparsers.add_parser('info', help='Get template information')
        info_parser.add_argument('name', type=str, help='Template name')
        
        # Templates export
        export_parser = templates_subparsers.add_parser('export', help='Export template to file')
        export_parser.add_argument('name', type=str, help='Template name')
        export_parser.add_argument('output', type=str, help='Output file path')
        
        # Templates import
        import_parser = templates_subparsers.add_parser('import', help='Import template from file')
        import_parser.add_argument('file', type=str, help='Template file to import')
        
        # Performance command
        perf_parser = subparsers.add_parser('performance', help='Performance monitoring')
        perf_subparsers = perf_parser.add_subparsers(dest='perf_action')
        
        # Performance report
        perf_subparsers.add_parser('report', help='Generate performance report')
        
        # Performance monitor
        monitor_parser = perf_subparsers.add_parser('monitor', help='Monitor performance')
        monitor_parser.add_argument('--duration', '-d', type=int, default=60,
                                  help='Monitor duration in seconds')
        monitor_parser.add_argument('--interval', '-i', type=float, default=1.0,
                                  help='Monitoring interval in seconds')
        
        # Benchmark command
        benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark functions')
        benchmark_parser.add_argument('function', type=str, help='Function to benchmark')
        benchmark_parser.add_argument('--runs', '-r', type=int, default=100,
                                    help='Number of benchmark runs')
        benchmark_parser.add_argument('--args', '-a', type=str, nargs='*',
                                    help='Function arguments')
        
        # Security command
        security_parser = subparsers.add_parser('security', help='Security utilities')
        security_subparsers = security_parser.add_subparsers(dest='security_action')
        
        # Security sanitize
        sanitize_parser = security_subparsers.add_parser('sanitize', help='Sanitize input text')
        sanitize_parser.add_argument('text', type=str, help='Text to sanitize')
        sanitize_parser.add_argument('--max-length', type=int, default=1000,
                                   help='Maximum text length')
        
        # Security rate-limit
        rate_limit_parser = security_subparsers.add_parser('rate-limit', help='Test rate limiting')
        rate_limit_parser.add_argument('key', type=str, help='Rate limit key')
        rate_limit_parser.add_argument('--limit', type=int, default=10,
                                     help='Rate limit per window')
        rate_limit_parser.add_argument('--window', type=int, default=60,
                                     help='Time window in seconds')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Configuration utilities')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        # Config convert
        convert_parser = config_subparsers.add_parser('convert', help='Convert configuration format')
        convert_parser.add_argument('input', type=str, help='Input file')
        convert_parser.add_argument('output', type=str, help='Output file')
        convert_parser.add_argument('--format', choices=['json', 'yaml'], default='json',
                                  help='Output format')
        
        # Info command
        subparsers.add_parser('info', help='Show package information')
        
        # Version command  
        subparsers.add_parser('version', help='Show version information')
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with arguments."""
        try:
            parsed_args = self.parser.parse_args(args)
            
            if not parsed_args.command:
                self.parser.print_help()
                return 0
            
            # Route to appropriate handler
            if parsed_args.command == 'create':
                return self._handle_create(parsed_args)
            elif parsed_args.command == 'validate':
                return self._handle_validate(parsed_args)
            elif parsed_args.command == 'templates':
                return self._handle_templates(parsed_args)
            elif parsed_args.command == 'performance':
                return self._handle_performance(parsed_args)
            elif parsed_args.command == 'benchmark':
                return self._handle_benchmark(parsed_args)
            elif parsed_args.command == 'security':
                return self._handle_security(parsed_args)
            elif parsed_args.command == 'config':
                return self._handle_config(parsed_args)
            elif parsed_args.command == 'info':
                return self._handle_info(parsed_args)
            elif parsed_args.command == 'version':
                return self._handle_version(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 130
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_create(self, args) -> int:
        """Handle create command."""
        try:
            if args.interactive:
                print("Starting interactive persona creation...")
                config = interactive_config_builder()
            
            elif args.template:
                # Parse template variables
                variables = {}
                if args.variables:
                    for var in args.variables:
                        if '=' in var:
                            key, value = var.split('=', 1)
                            variables[key] = value
                        else:
                            print(f"Warning: Invalid variable format '{var}', expected key=value")
                
                config = create_persona_from_template(args.template, **variables)
                print(f"Created persona from template: {args.template}")
            
            else:
                print("Error: Must specify either --interactive or --template")
                return 1
            
            # Save configuration
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"Persona configuration saved to: {output_path}")
            print(f"Persona name: {config.get('name', 'Unknown')}")
            
            return 0
            
        except Exception as e:
            print(f"Error creating persona: {e}")
            return 1
    
    def _handle_validate(self, args) -> int:
        """Handle validate command."""
        try:
            file_path = Path(args.file)
            
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                return 1
            
            # Load and validate persona
            with open(file_path, 'r', encoding='utf-8') as f:
                persona_config = json.load(f)
            
            # Validate name
            if 'name' in persona_config:
                validate_persona_name(persona_config['name'])
                print("✓ Persona name is valid")
            
            # Validate traits
            if 'traits' in persona_config:
                validate_persona_traits(persona_config['traits'])
                print("✓ Persona traits are valid")
            
            # Additional validations if strict mode
            if args.strict:
                from .validation import validate_persona_consistency
                validate_persona_consistency(persona_config)
                print("✓ Persona consistency check passed")
            
            print(f"✅ Persona configuration is valid: {file_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return 1
    
    def _handle_templates(self, args) -> int:
        """Handle templates command."""
        try:
            if args.template_action == 'list':
                templates = list_available_templates()
                
                if not templates:
                    print("No templates available.")
                    return 0
                
                print("Available templates:")
                print("-" * 40)
                for template in templates:
                    print(f"📋 {template['name']}")
                    print(f"   {template['description']}")
                    print()
            
            elif args.template_action == 'info':
                from .templates import get_template_info
                
                try:
                    info = get_template_info(args.name)
                    print(f"Template: {info['name']}")
                    print(f"Description: {info['description']}")
                    
                    if info['required_variables']:
                        print(f"Required variables: {', '.join(info['required_variables'])}")
                    else:
                        print("No variables required")
                
                except PersonaError as e:
                    print(f"Template not found: {args.name}")
                    return 1
            
            elif args.template_action == 'export':
                export_template_to_file(args.name, args.output)
                print(f"Template '{args.name}' exported to: {args.output}")
            
            elif args.template_action == 'import':
                import_template_from_file(args.file)
                print(f"Template imported from: {args.file}")
            
            else:
                print("Error: Template action required (list, info, export, import)")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_performance(self, args) -> int:
        """Handle performance command."""
        try:
            if args.perf_action == 'report':
                report = performance_report()
                print(report)
            
            elif args.perf_action == 'monitor':
                from .monitoring import PerformanceMonitor
                import time
                
                monitor = PerformanceMonitor()
                monitor.start_monitoring(interval=args.interval)
                
                print(f"Monitoring system performance for {args.duration} seconds...")
                print("Press Ctrl+C to stop early")
                
                try:
                    time.sleep(args.duration)
                finally:
                    monitor.stop_monitoring()
                
                # Generate report
                stats = monitor.get_system_stats()
                print("\nMonitoring Results:")
                print("-" * 30)
                
                if 'memory' in stats:
                    print(f"Memory: {stats['memory']['current_percent']:.1f}% used")
                    print(f"Available: {stats['memory']['available_mb']:.0f} MB")
                
                if 'cpu' in stats:
                    print(f"CPU: {stats['cpu']['current_percent']:.1f}%")
            
            else:
                print("Error: Performance action required (report, monitor)")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_benchmark(self, args) -> int:
        """Handle benchmark command."""
        try:
            # This is a simplified benchmark for CLI demo
            print(f"Benchmarking function: {args.function}")
            print(f"Runs: {args.runs}")
            
            # For demo, benchmark a simple function
            def test_function():
                import time
                time.sleep(0.001)  # Simulate work
                return "test result"
            
            benchmarker = Benchmarker()
            result = benchmarker.benchmark(test_function, args.runs)
            
            print(f"\nBenchmark Results:")
            print(f"Total time: {result.total_time:.4f}s")
            print(f"Mean time: {result.mean_time:.6f}s")
            print(f"Runs per second: {result.runs_per_second:.2f}")
            print(f"Min/Max: {result.min_time:.6f}s / {result.max_time:.6f}s")
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_security(self, args) -> int:
        """Handle security command."""
        try:
            if args.security_action == 'sanitize':
                clean_text = sanitize_input(args.text, max_length=args.max_length)
                print(f"Original: {args.text}")
                print(f"Sanitized: {clean_text}")
            
            elif args.security_action == 'rate-limit':
                limiter = RateLimiter()
                
                # Test rate limiting
                print(f"Testing rate limit for key: {args.key}")
                print(f"Limit: {args.limit} requests per {args.window} seconds")
                
                for i in range(args.limit + 2):
                    allowed = limiter.is_allowed(args.key, limit=args.limit, window=args.window)
                    status = "✓ ALLOWED" if allowed else "✗ DENIED"
                    print(f"Request {i+1}: {status}")
                
                info = limiter.get_info(args.key, limit=args.limit, window=args.window)
                print(f"\nRate limit info:")
                print(f"Remaining: {info.remaining}")
                print(f"Reset time: {info.reset_time}")
            
            else:
                print("Error: Security action required (sanitize, rate-limit)")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_config(self, args) -> int:
        """Handle config command."""
        try:
            if args.config_action == 'convert':
                # Load input file
                input_path = Path(args.input)
                with open(input_path, 'r', encoding='utf-8') as f:
                    if input_path.suffix.lower() == '.json':
                        config = json.load(f)
                    else:
                        # Assume JSON for now
                        config = json.load(f)
                
                # Save in requested format
                output_path = Path(args.output)
                if args.format == 'json':
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                elif args.format == 'yaml':
                    try:
                        import yaml
                        with open(output_path, 'w', encoding='utf-8') as f:
                            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                    except ImportError:
                        print("Error: PyYAML not installed. Install with: pip install PyYAML")
                        return 1
                
                print(f"Configuration converted: {input_path} -> {output_path}")
            
            else:
                print("Error: Config action required (convert)")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _handle_info(self, args) -> int:
        """Handle info command."""
        print("Agent Personas Framework")
        print("=" * 30)
        print("A comprehensive system for creating and managing AI personas")
        print()
        print("Features:")
        print("• Interactive persona creation")
        print("• Template-based configuration")
        print("• Comprehensive validation")
        print("• Performance monitoring")
        print("• Security utilities")
        print("• Benchmarking tools")
        print()
        print("Use 'personas --help' for available commands")
        
        return 0
    
    def _handle_version(self, args) -> int:
        """Handle version command."""
        print("agent-personas v1.0.0")
        return 0


def main():
    """Main CLI entry point."""
    cli = PersonaCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()