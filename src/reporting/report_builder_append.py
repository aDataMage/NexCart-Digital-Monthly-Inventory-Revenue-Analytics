
    def _build_executive_summary(self):
        """Generate LLM-based executive summary PowerPoint."""
        logger.info("Generating Executive Summary with LLM...")
        
        try:
            # Generate insights with LLM
            llm_client = LLMClient()
            insights = llm_client.generate_insights(self.aggregated_data)
            
            # Generate PowerPoint
            pptx_generator = ExecutiveSummaryGenerator()
            pptx_path = self.output_dir / 'executive_summary.pptx'
            
            pptx_generator.generate_presentation(
                insights=insights,
                report_data=self.aggregated_data,
                output_path=str(pptx_path)
            )
            
            logger.info(f"Executive summary PowerPoint created: {pptx_path}")
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            logger.warning("Continuing without executive summary...")
